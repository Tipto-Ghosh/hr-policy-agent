from typing import Literal
from pydantic import BaseModel, Field


__all__ = [
    "Route",
    "_ScopeDecision",
    "EvidenceGrade",
    "GroundednessResult"
]

class Route(BaseModel):
    """A route to a specific node in the agent's workflow."""

    route: Literal["knowledge_base", "direct_answer"] = Field(
        description = "The route to take based on the question."
    )
    
    
class _ScopeDecision(BaseModel):
    in_scope: bool = Field(
        description = "True if the question is HR/organizational in scope."
    )

class EvidenceGrade(BaseModel):
    """A grade for the evidence based on its ability to answer the question."""

    grade: Literal["good", "weak"] = Field(
        description = "good if the evidence can answer the question; weak otherwise."
    )
    
class GroundednessResult(BaseModel):
    grounded: bool = Field(..., description="Whether the answer is grounded in the context")
