from enum import Enum
from typing import Annotated, List
from pydantic import BaseModel, Field, ConfigDict

class Category(BaseModel):
  name: Annotated[str, Field(
    min_length=2,
    max_length=60,
    description="Category name (specific interpretation, e.g., 'roofing_repair_service_request')."
  )]

  confidence: Annotated[float, Field(
    ge=0, le=100,
    description="Confidence score (0–100) estimating how strongly this category applies."
  )]

  reasoning: Annotated[str, Field(
    min_length=5, max_length=160,
    description="One concise sentence explaining the rationale for the categorization."
  )]

class FixedCategory(str, Enum):

  real_estate_agent = "real_estate_agent"
  electrician = "electrician"
  roofing = "roofing"
  mechanic = "mechanic"

class DiscoverCategory(BaseModel):
  items: Annotated[List[Category], Field(
    min_length=5,
    max_length=5,
    description="Exactly five category interpretations ranked by likelihood or relevance."
  )]

  fixed_category: Annotated[FixedCategory, Field(
    description="A final simplified category derived from the highest-confidence or most representative item in `items`."
  )]

  model_config = ConfigDict(
    json_schema_extra={
      "examples": [
        {
          "items": [
            {
              "name": "roofing_repair_service_request",
              "confidence": 94.2,
              "reasoning": "User explicitly asks for quotes to fix damage on their home's roof."
            },
            {
              "name": "storm_damage_home_restoration",
              "confidence": 88.9,
              "reasoning": "Mentions storm damage and urgency for repair services."
            },
            {
              "name": "contractor_shortlist_evaluation",
              "confidence": 82.3,
              "reasoning": "User is comparing multiple roofing contractors based on cost/quality."
            },
            {
              "name": "trustworthiness_reputation_check",
              "confidence": 74.5,
              "reasoning": "User asks for reviews and reputation info rather than just availability."
            },
            {
              "name": "general_home_repair_discussion",
              "confidence": 63.1,
              "reasoning": "Conversation includes broader advice beyond immediate contracting."
            }
          ],
          "fixed_category": "roofing"
        }
      ]
    }
  )
