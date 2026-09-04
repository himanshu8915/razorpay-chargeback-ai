import os
import json
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class DemoPortfolioResolver:
    """
    Centralized resolver for the Phase 7 live demo portfolio manifest.
    Responsibilities:
    - Load and validate the manifest (phase7_allocation_master.json)
    - Resolve selected merchant
    - Return live_demo_case_ids
    - Cache the parsed manifest in memory
    """
    _cache = None
    _MANIFEST_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
        "results", "phase7", "phase7_allocation_master.json"
    )

    @classmethod
    def _load_manifest(cls) -> Optional[dict]:
        if cls._cache is not None:
            return cls._cache

        if not os.path.exists(cls._MANIFEST_PATH):
            logger.error(f"Manifest file not found at {cls._MANIFEST_PATH}")
            return None

        try:
            with open(cls._MANIFEST_PATH, "r") as f:
                cls._cache = json.load(f)
            return cls._cache
        except Exception as e:
            logger.error(f"Failed to load manifest: {e}")
            return None

    @classmethod
    def get_live_demo_case_ids(cls, merchant_id: str) -> List[str]:
        """
        Returns the list of dispute IDs in the live_demo_pool for the specified merchant.
        If the manifest cannot be loaded or the merchant is not found, returns an empty list.
        """
        manifest = cls._load_manifest()
        if not manifest:
            return []

        merchants = manifest.get("merchants", {})
        merchant_data = merchants.get(merchant_id)
        if not merchant_data:
            return []

        return merchant_data.get("live_demo_pool", [])
