import asyncio
from sqlalchemy import select, text
from app.db.session import AsyncSessionLocal
from app.db.models import Dispute, DecisionArtifactModel
from app.evidence.services.evidence_discovery_service import EvidenceDiscoveryService
from app.evidence.services.evidence_verification_service import EvidenceVerificationService
from app.decision.services.decision_service import DecisionService
from app.decision.models.decision import FinalDecision

async def run_experiment():
    async with AsyncSessionLocal() as db:
        dispute_id = 'DSP_000001'
        print(f"Running full Phase 3/4/5 analysis on {dispute_id}")
        
        # Phase 3
        discovery_service = EvidenceDiscoveryService(db)
        bundle, _ = await discovery_service.discover_evidence(dispute_id)
        canonical_case = await discovery_service.case_service.get_case(dispute_id)
        print("Phase 3 complete.")
        
        # Phase 4
        verification_service = EvidenceVerificationService()
        assessment, _ = await verification_service.verify_evidence(canonical_case, bundle)
        print("Phase 4 complete.")
        
        # Phase 5
        decision_service = DecisionService()
        result = await decision_service.analyze_dispute(dispute_id, canonical_case, assessment, [])
        print("Phase 5 complete.")
        
        decision_artifact = await decision_service.get_decision(dispute_id)
        print(f"Decision: {decision_artifact.get('ai_recommendation')} - Confidence: {decision_artifact.get('confidence')}")
        

        
if __name__ == "__main__":
    asyncio.run(run_experiment())
