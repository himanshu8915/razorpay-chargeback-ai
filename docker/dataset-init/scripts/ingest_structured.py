import os
import psycopg
import polars as pl
from logger import log_event

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/chargeback")
# Note: psycopg3 requires postgresql:// instead of postgresql+asyncpg://
DATABASE_URL_SYNC = DATABASE_URL.replace("+asyncpg", "")
DOWNLOAD_DIR = "/data/raw"

def ingest_table(conn, table_name, csv_file):
    try:
        csv_path = os.path.join(DOWNLOAD_DIR, csv_file)
        if not os.path.exists(csv_path):
            # Sometimes Kaggle extracts into a subdirectory
            for root, dirs, files in os.walk(DOWNLOAD_DIR):
                if csv_file in files:
                    csv_path = os.path.join(root, csv_file)
                    break
                    
        df = pl.read_csv(csv_path, infer_schema_length=10000, null_values=["", "NaN", "null"])
        columns = df.columns
        columns_str = ", ".join(columns)
        
        # Write to postgres using psycopg3 COPY
        with conn.cursor() as cur:
            with cur.copy(f"COPY {table_name} ({columns_str}) FROM STDIN") as copy:
                for row in df.iter_rows():
                    copy.write_row(row)
        conn.commit()
        log_event("STRUCTURED_INGESTION", "SUCCESS", f"Ingested {len(df)} rows into {table_name}.")
    except Exception as e:
        log_event("STRUCTURED_INGESTION", "FAILED", f"Failed to ingest {table_name}: {str(e)}")
        raise

def run_structured_ingestion():
    log_event("STRUCTURED_INGESTION", "INFO", "Starting structured data ingestion...")
    try:
        with psycopg.connect(DATABASE_URL_SYNC) as conn:
            ingest_table(conn, "customers", "customers.csv")
            ingest_table(conn, "merchants", "merchants.csv")
            ingest_table(conn, "orders", "orders.csv")
            ingest_table(conn, "transactions", "transactions.csv")
            ingest_table(conn, "deliveries", "deliveries.csv")
            ingest_table(conn, "disputes", "disputes.csv")
        return True
    except Exception as e:
        log_event("STRUCTURED_INGESTION", "FAILED", "Structured ingestion aborted.")
        return False

if __name__ == "__main__":
    run_structured_ingestion()
