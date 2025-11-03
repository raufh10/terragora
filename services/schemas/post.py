from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict


class PostCategory(BaseModel):

  is_lead: Annotated[bool, Field(
    description="Indicates whether this post is a potential business lead (True) or a general/non-lead post (False)."
  )]

  label: Annotated[str, Field(
    min_length=2, max_length=60,
    description=(
      "If is_lead=True, this field describes the type or name of the business lead (e.g. 'tree removal', 'lawn care'). "
      "If is_lead=False, it describes a general category like 'discussion' or 'question'."
    )
  )]

  confidence: Annotated[float, Field(
    ge=0, le=100,
    description="Confidence score (0–100) reflecting certainty in this classification."
  )]

  model_config = ConfigDict(
    json_schema_extra={
      "examples": [
        {
          "is_lead": True,
          "label": "tree removal",
          "confidence": 91.8
        },
        {
          "is_lead": False,
          "label": "discussion",
          "confidence": 76.5
        }
      ]
    }
  )
