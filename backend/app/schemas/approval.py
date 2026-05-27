from datetime import datetime
from uuid import UUID
from typing import Any
from pydantic import BaseModel, ConfigDict, model_validator

class ApprovedSolutionResponse(BaseModel):
    id: UUID
    problem_id: UUID
    title: str
    description: str
    mechanism: str | None = None
    tech_stack: list[str] | None = None
    target_user: str | None = None
    revenue_model: str | None = None
    is_unconventional: bool
    status: str
    created_at: datetime
    updated_at: datetime
    
    # Problem Statement Context
    problem_title: str
    industry: str
    location: str
    
    # Evaluation Metrics
    weighted_avg: float | None = None
    min_score: float | None = None
    attack_survives: bool | None = None
    inconsistency_count: int | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def populate_context(cls, data: Any) -> Any:
        if hasattr(data, "__dict__"):
            # ORM object
            prob = getattr(data, "problem_statement", None)
            session = getattr(prob, "session", None) if prob else None
            eval_obj = getattr(data, "evaluation", None)
            
            # Since Pydantic from_attributes gets attributes, we can construct a dictionary of the values
            res = {}
            for field in cls.model_fields:
                if hasattr(data, field):
                    res[field] = getattr(data, field)
            
            res["problem_title"] = getattr(prob, "title", "") if prob else ""
            res["industry"] = getattr(session, "industry", "") if session else ""
            res["location"] = getattr(session, "location", "") if session else ""
            
            res["weighted_avg"] = getattr(eval_obj, "weighted_avg", None) if eval_obj else None
            res["min_score"] = getattr(eval_obj, "min_score", None) if eval_obj else None
            res["attack_survives"] = getattr(eval_obj, "attack_survives", None) if eval_obj else None
            res["inconsistency_count"] = getattr(eval_obj, "inconsistency_count", 0) if eval_obj else 0
            return res
        elif isinstance(data, dict):
            # Dict representation
            prob = data.get("problem_statement", {})
            session = prob.get("session", {}) if isinstance(prob, dict) else getattr(prob, "session", None)
            eval_obj = data.get("evaluation", {})
            
            res = {**data}
            res["problem_title"] = prob.get("title", "") if isinstance(prob, dict) else getattr(prob, "title", "")
            res["industry"] = session.get("industry", "") if isinstance(session, dict) else getattr(session, "industry", "")
            res["location"] = session.get("location", "") if isinstance(session, dict) else getattr(session, "location", "")
            
            if isinstance(eval_obj, dict):
                res["weighted_avg"] = eval_obj.get("weighted_avg")
                res["min_score"] = eval_obj.get("min_score")
                res["attack_survives"] = eval_obj.get("attack_survives")
                res["inconsistency_count"] = eval_obj.get("inconsistency_count", 0)
            else:
                res["weighted_avg"] = getattr(eval_obj, "weighted_avg", None)
                res["min_score"] = getattr(eval_obj, "min_score", None)
                res["attack_survives"] = getattr(eval_obj, "attack_survives", None)
                res["inconsistency_count"] = getattr(eval_obj, "inconsistency_count", 0)
            return res
        return data
