import os
import psycopg
import concurrent.futures
from datetime import datetime
from logger import init_logger, log_event
from download import download_datasets
from ingest_structured import run_structured_ingestion
from ingest_policies import run_policy_ingestion
from verify import run_verification

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/chargeback")
DATABASE_URL_SYNC = DATABASE_URL.replace("+asyncpg", "")

def is_ready():
    try:
        with psycopg.connect(DATABASE_URL_SYNC) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM system_metadata WHERE key = 'status'")
                row = cur.fetchone()
                if row and row[0] == 'READY':
                    return True
        return False
    except Exception as e:
        # Table might not exist or other error, assume not ready
        return False

def set_ready():
    try:
        with psycopg.connect(DATABASE_URL_SYNC) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO system_metadata (key, value, updated_at) 
                    VALUES ('status', 'READY', %s) 
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at
                """, (datetime.utcnow(),))
            conn.commit()
    except Exception as e:
        log_event("DATABASE", "FAILED", f"Could not set READY state: {str(e)}")
        raise

def set_failed():
    try:
        with psycopg.connect(DATABASE_URL_SYNC) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO system_metadata (key, value, updated_at) 
                    VALUES ('status', 'FAILED', %s) 
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at
                """, (datetime.utcnow(),))
            conn.commit()
    except Exception as e:
        pass

def main():
    init_logger()
    log_event("DATABASE", "INFO", "Checking initialization state...")
    
    if is_ready():
        log_event("DATABASE", "SUCCESS", "System is already READY. Skipping initialization.")
        return
        
    log_event("DATABASE", "INFO", "System NOT READY. Starting initialization.")
    
    # 1. Download
    if not download_datasets():
        set_failed()
        return

    # 2. Parallel Ingestion
    log_event("DATABASE", "INFO", "Starting parallel ingestion pipelines...")
    structured_success = False
    policy_success = False
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_pipeline = {
            executor.submit(run_structured_ingestion): "STRUCTURED",
            executor.submit(run_policy_ingestion): "POLICY"
        }
        for future in concurrent.futures.as_completed(future_to_pipeline):
            pipeline_name = future_to_pipeline[future]
            try:
                result = future.result()
                if pipeline_name == "STRUCTURED":
                    structured_success = result
                else:
                    policy_success = result
            except Exception as exc:
                log_event("DATABASE", "FAILED", f"{pipeline_name} pipeline generated an exception: {exc}")
    
    if not structured_success or not policy_success:
        log_event("DATABASE", "FAILED", "One or more pipelines failed. Marking state as FAILED.")
        set_failed()
        return
        
    # 3. Verification
    if not run_verification():
        set_failed()
        return
        
    # 4. Mark Ready
    set_ready()
    log_event("READY", "SUCCESS", "Initialization complete and verified.")

if __name__ == "__main__":
    main()
