from typing import List, Optional, Dict
from pydantic import BaseModel, Field, HttpUrl, field_validator

# --- Input Models ---

class CandidateProfile(BaseModel):
    id: str = Field(..., description="Unique identifier for the candidate (e.g., LinkedIn URL or hash)")
    name: str = Field(..., description="Full name of the candidate")
    headline: Optional[str] = Field(None, description="LinkedIn Headline or Professional Summary")
    location: Optional[str] = Field(None, description="Candidate location")
    profile_url: Optional[str] = Field(None, description="URL to LinkedIn profile")
    about: Optional[str] = Field(None, description="Full 'About' section text")
    experience_text: Optional[str] = Field(None, description="Concatenated text of experience entries")
    education_text: Optional[str] = Field(None, description="Concatenated text of education entries")
    
    # Optional metadata not always available from simple search
    raw_resume_text: Optional[str] = Field(None, description="Full text extracted from PDF resume")
    is_open_to_work: bool = Field(False, description="Whether the candidate has the 'Open to Work' badge/status")


# --- Output / Scoring Models ---

class RoleFitScore(BaseModel):
    score: int = Field(..., ge=0, le=100, description="0-100 score of how well they match the specific role")
    strengths: List[str] = Field(default_factory=list, description="Key skills or experiences that match")
    gaps: List[str] = Field(default_factory=list, description="Missing skills or red flags")
    evidence: Optional[str] = Field(None, description="Direct quotes or summary of experience justifying the score")
    explanation: Optional[str] = Field(None, description="Brief explanation of the fit score")

    @field_validator('evidence', 'explanation', mode='before')
    @classmethod
    def convert_to_string(cls, v):
        if v is None:
            return v
        if isinstance(v, (dict, list)):
            import json
            return json.dumps(v, indent=2)
        return str(v)

    @field_validator('strengths', 'gaps', mode='before')
    @classmethod
    def convert_to_list(cls, v):
        if v is None:
            return []
        
        # If it's already a list, process each item
        if isinstance(v, list):
            processed = []
            for item in v:
                if isinstance(item, dict):
                    # extract 'requirement' or 'value' or just first value
                    val = item.get('requirement') or item.get('value') or item.get('item') or list(item.values())[0] if item.values() else str(item)
                    processed.append(str(val))
                else:
                    processed.append(str(item))
            return processed

        if isinstance(v, str):
            # If AI returned a single string, wrap it in a list
            import re
            items = [s.strip() for s in re.split(r'[,;\n]', v) if s.strip()]
            return items if items else [v]
        
        return [str(v)]

class CandidateAssessment(BaseModel):
    candidate_id: str
    candidate_name: str = Field(..., description="Full name of the candidate")
    overall_score: int = Field(..., ge=0, le=100)
    tier: int = Field(..., ge=1, le=3, description="1=Best, 2=Good, 3=Average")
    recommended_action: str = Field(..., pattern="^(Shortlist|Review|Hold|Reject)$")
    
    role_fit_analysis: RoleFitScore
    
    reasoning_summary: str = Field(..., description="Executive summary of why this candidate was ranked this way")
    risk_flags: List[str] = Field(default_factory=list, description="Potential concerns (e.g., job hopping, employment gaps)")
    
    @field_validator('risk_flags', mode='before')
    @classmethod
    def convert_risk_flags_to_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            import re
            return [s.strip() for s in re.split(r'[,;\n]', v) if s.strip()]
        if not isinstance(v, list):
            return [str(v)]
        return [str(i) for i in v]

    # Metadata for transparency
    model_used: str = "gpt-4o" 
