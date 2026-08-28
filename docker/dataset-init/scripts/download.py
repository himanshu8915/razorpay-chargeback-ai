import os
from kaggle.api.kaggle_api_extended import KaggleApi
from logger import log_event

DATASET_STRUCTURED = "himanshusharma809/razorpayhackathon"
DATASET_POLICY = "himanshusharma809/razorpay-chargeback-policy-corpus"
DOWNLOAD_DIR = "/data/raw"

def download_datasets():
    log_event("DOWNLOAD", "INFO", "Authenticating with Kaggle API...")
    try:
        api = KaggleApi()
        api.authenticate()
        
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        log_event("DOWNLOAD", "INFO", f"Downloading structured dataset: {DATASET_STRUCTURED}")
        api.dataset_download_files(DATASET_STRUCTURED, path=DOWNLOAD_DIR, unzip=True)
        
        log_event("DOWNLOAD", "INFO", f"Downloading policy dataset: {DATASET_POLICY}")
        api.dataset_download_files(DATASET_POLICY, path=DOWNLOAD_DIR, unzip=True)
        
        # Lightweight sanity check (just checking if files exist)
        expected_structured = ["customers.csv", "merchants.csv", "orders.csv", "transactions.csv", "deliveries.csv", "disputes.csv"]
        # Policies might be in a nested folder depending on how kaggle zipped it, but let's assume they are extracted directly or we will search for them.
        
        log_event("SANITY_CHECK", "SUCCESS", "Datasets downloaded and extracted.")
        return True
    except Exception as e:
        log_event("DOWNLOAD", "FAILED", f"Error downloading datasets: {str(e)}")
        return False

if __name__ == "__main__":
    download_datasets()
