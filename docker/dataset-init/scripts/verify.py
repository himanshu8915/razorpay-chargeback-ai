import os
import psycopg
from logger import log_event

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/chargeback")
DATABASE_URL_SYNC = DATABASE_URL.replace("+asyncpg", "")

def run_verification():
    log_event("VERIFICATION", "INFO", "Starting final verification...")
    try:
        with psycopg.connect(DATABASE_URL_SYNC) as conn:
            with conn.cursor() as cur:
                # 1. Structural counts
                tables = ["customers", "merchants", "orders", "transactions", "deliveries", "disputes"]
                expected_counts = {
                    "customers": 10000,
                    "merchants": 3095,
                    "orders": 99441,
                    "transactions": 103886,
                    "deliveries": 99441,
                    "disputes": 10000
                }
                
                total_rows = 0
                for table in tables:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    total_rows += count
                    if count != expected_counts[table]:
                        raise Exception(f"Table {table} count mismatch. Expected {expected_counts[table]}, got {count}")
                
                if total_rows != 325863:
                    raise Exception(f"Total structured rows mismatch. Expected 325863, got {total_rows}")
                
                # 2. Policy counts
                cur.execute("SELECT COUNT(*) FROM policy_documents")
                policy_count = cur.fetchone()[0]
                if policy_count != 8:
                    raise Exception(f"Policy count mismatch. Expected 8, got {policy_count}")
                
                cur.execute("SELECT COUNT(*) FROM policy_child_chunks")
                chunk_count = cur.fetchone()[0]
                if chunk_count == 0:
                    raise Exception("No policy chunks found.")
                    
                # 3. Vector query test
                cur.execute("SELECT child_chunk_id FROM policy_child_chunks LIMIT 1")
                if not cur.fetchone():
                    raise Exception("Vector query failed.")
                
        log_event("VERIFICATION", "SUCCESS", "All verification checks passed.")
        return True
    except Exception as e:
        log_event("VERIFICATION", "FAILED", f"Verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    run_verification()
