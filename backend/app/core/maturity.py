from enum import Enum
from pydantic import BaseModel

class MaturityLevel(str, Enum):
    POC = "poc"
    MVP = "mvp"
    PRE_PRODUCTION = "pre_production"
    PRODUCTION = "production"

class MaturityConfig(BaseModel):
    level: MaturityLevel
    label: str
    pain_point_count: tuple[int, int]  # (min, max)
    problem_statement_count: int
    solution_candidate_count: int
    evaluation_steps: list[str]  # which evaluation steps to run
    temperature: float
    include_security_criteria: bool
    include_compliance_criteria: bool
    description: str

MATURITY_CONFIGS: dict[MaturityLevel, MaturityConfig] = {
    MaturityLevel.POC: MaturityConfig(
        level=MaturityLevel.POC,
        label="Proof of Concept",
        pain_point_count=(3, 3),
        problem_statement_count=2,
        solution_candidate_count=3,
        evaluation_steps=["rubric_scoring"],
        temperature=0.9,
        include_security_criteria=False,
        include_compliance_criteria=False,
        description="Quick validation, speed over rigor",
    ),
    MaturityLevel.MVP: MaturityConfig(
        level=MaturityLevel.MVP,
        label="Minimum Viable Product",
        pain_point_count=(5, 5),
        problem_statement_count=2,
        solution_candidate_count=4,
        evaluation_steps=["rubric_scoring", "devils_advocate"],
        temperature=0.7,
        include_security_criteria=False,
        include_compliance_criteria=False,
        description="Balanced depth, core features focus",
    ),
    MaturityLevel.PRE_PRODUCTION: MaturityConfig(
        level=MaturityLevel.PRE_PRODUCTION,
        label="Pre-Production",
        pain_point_count=(6, 8),
        problem_statement_count=3,
        solution_candidate_count=5,
        evaluation_steps=["rubric_scoring", "devils_advocate", "ach_analysis", "consistency_check", "rating_aggregation"],
        temperature=0.5,
        include_security_criteria=False,
        include_compliance_criteria=False,
        description="Full rigor, production considerations",
    ),
    MaturityLevel.PRODUCTION: MaturityConfig(
        level=MaturityLevel.PRODUCTION,
        label="Production-Grade",
        pain_point_count=(8, 10),
        problem_statement_count=3,
        solution_candidate_count=5,
        evaluation_steps=["rubric_scoring", "devils_advocate", "ach_analysis", "consistency_check", "rating_aggregation", "security_check", "compliance_check"],
        temperature=0.3,
        include_security_criteria=True,
        include_compliance_criteria=True,
        description="Enterprise-ready, compliance, security focus",
    ),
}

def get_maturity_config(level: MaturityLevel) -> MaturityConfig:
    return MATURITY_CONFIGS[level]
