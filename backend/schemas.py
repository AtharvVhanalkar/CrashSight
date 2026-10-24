from pydantic import BaseModel

# Schema for the incoming GitHub dispatch request
class DispatchRequest(BaseModel):
    app_name: str
    report_markdown: str

# Schemas for Gemma 4's strict JSON output
class PrimaryDiagnosis(BaseModel):
    error_class: str
    confidence_score: str
    severity: str
    fault_location: str

class RecommendedMitigation(BaseModel):
    safe_command: str

class TriageResponse(BaseModel):
    primary_diagnosis: PrimaryDiagnosis
    probable_root_cause: str
    recommended_mitigation: RecommendedMitigation