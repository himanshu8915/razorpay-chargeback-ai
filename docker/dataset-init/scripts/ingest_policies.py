import os
import glob
import fitz  # PyMuPDF
import psycopg
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid
from logger import log_event

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/chargeback")
DATABASE_URL_SYNC = DATABASE_URL.replace("+asyncpg", "")
DOWNLOAD_DIR = "/data/raw"

def run_policy_ingestion():
    log_event("POLICY_EXTRACTION", "INFO", "Starting policy document processing...")
    
    try:
        # Load embedding model
        model = SentenceTransformer('BAAI/bge-small-en-v1.5')
        
        parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
        child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)

        # Find PDF files (might be nested)
        pdf_files = []
        for root, dirs, files in os.walk(DOWNLOAD_DIR):
            for file in files:
                if file.endswith(".pdf"):
                    pdf_files.append(os.path.join(root, file))
        
        if len(pdf_files) != 8:
            log_event("POLICY_EXTRACTION", "INFO", f"Expected 8 policies, found {len(pdf_files)}.")
            # If not 8, we still proceed but note it. The validation script will assert 8 later.
        
        with psycopg.connect(DATABASE_URL_SYNC) as conn:
            with conn.cursor() as cur:
                for pdf_path in pdf_files:
                    filename = os.path.basename(pdf_path)
                    policy_id = filename.replace('.pdf', '')
                    
                    # 1. Insert Policy Document
                    cur.execute(
                        "INSERT INTO policy_documents (policy_id, title, source_file, version) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                        (policy_id, policy_id, filename, "1.0")
                    )
                    
                    # 2. Extract Text
                    doc = fitz.open(pdf_path)
                    text = ""
                    for page in doc:
                        text += page.get_text() + "\n"
                    
                    # 3. Chunking
                    parent_chunks = parent_splitter.split_text(text)
                    for p_chunk in parent_chunks:
                        parent_id = str(uuid.uuid4())
                        cur.execute(
                            "INSERT INTO policy_parent_chunks (parent_chunk_id, policy_id, content, page) VALUES (%s, %s, %s, %s)",
                            (parent_id, policy_id, p_chunk, 1) # Simplification for page
                        )
                        
                        child_chunks = child_splitter.split_text(p_chunk)
                        
                        # 4. Embeddings & Child Insert
                        embeddings = model.encode(child_chunks)
                        for c_chunk, emb in zip(child_chunks, embeddings):
                            child_id = str(uuid.uuid4())
                            cur.execute(
                                "INSERT INTO policy_child_chunks (child_chunk_id, parent_chunk_id, policy_id, content, embedding) VALUES (%s, %s, %s, %s, %s)",
                                (child_id, parent_id, policy_id, c_chunk, emb.tolist())
                            )
            conn.commit()
            
        log_event("POLICY_EXTRACTION", "SUCCESS", f"Processed {len(pdf_files)} policies with embeddings.")
        return True
    except Exception as e:
        log_event("POLICY_EXTRACTION", "FAILED", f"Error processing policies: {str(e)}")
        return False

if __name__ == "__main__":
    run_policy_ingestion()
