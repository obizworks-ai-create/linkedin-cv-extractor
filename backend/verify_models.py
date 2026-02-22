from src.models import CandidateAssessment, RoleFitScore
import json

# Test data for Misbah Imran-style failure (string instead of list)
test_data = {
    "candidate_id": "test_id",
    "candidate_name": "Test Candidate",
    "overall_score": 85,
    "tier": 1,
    "recommended_action": "Shortlist",
    "role_fit_analysis": {
        "score": 85,
        "strengths": "Python, JavaScript", # String instead of list
        "gaps": ["None"],
        "evidence": "Works at Google"
    },
    "reasoning_summary": "Great fit.",
    "risk_flags": "Job hopping" # String instead of list
}

try:
    assessment = CandidateAssessment(**test_data)
    print("✅ Validation Successful")
    print(f"Strengths: {assessment.role_fit_analysis.strengths}")
    print(f"Risk Flags: {assessment.risk_flags}")
    
    # Verify they are lists
    assert isinstance(assessment.role_fit_analysis.strengths, list)
    assert isinstance(assessment.risk_flags, list)
    print("✅ List conversion verified")
    
except Exception as e:
    print(f"❌ Validation Failed: {e}")
