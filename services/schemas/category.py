from enum import Enum
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict

class SubmissionCategoryLabel(str, Enum):
  lead = "lead"
  relevant = "relevant"
  help = "help"
  question = "question"
  discussion = "discussion"

class SubmissionCategory(BaseModel):
  label: Annotated[SubmissionCategoryLabel, Field(
    description="Predicted category for the Reddit submission."
  )]
  confidence: Annotated[float, Field(
    ge=0, le=100,
    description="Confidence score (0–100) for the chosen label."
  )]
  rationale: Annotated[str, Field(
    min_length=5, max_length=120,
    description="One concise sentence explaining why this label fits."
  )]

  model_config = ConfigDict(
    json_schema_extra={
      "examples": [
        {"label": "lead", "confidence": 87.3,
         "rationale": "User is directly requesting a tree removal service."}
      ]
    }
  )
