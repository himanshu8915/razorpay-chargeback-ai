import json
import os
from fastapi import APIRouter, HTTPException, status

router = APIRouter(
    prefix="/merchants",
    tags=["Merchants"]
)

# Relative to the backend running directory, which is the root of the project usually.
MANIFEST_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "results", "phase7", "demo_portfolio_manifest.json")

@router.get("/portfolio")
async def get_portfolio():
    print(f"DEBUG: Checking MANIFEST_PATH={MANIFEST_PATH}")
    print(f"DEBUG: __file__={__file__}")
    print(f"DEBUG: os.getcwd()={os.getcwd()}")
    """Serves the Phase 7 demo portfolio manifest to the frontend."""
    if not os.path.exists(MANIFEST_PATH):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phase 7 demo_portfolio_manifest.json not found. Run materialization first."
        )
    try:
        with open(MANIFEST_PATH, "r") as f:
            manifest = json.load(f)
        return manifest
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read portfolio manifest: {str(e)}"
        )
