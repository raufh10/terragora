from typing import Annotated, List
from pydantic import BaseModel, Field, ConfigDict


class Category(BaseModel):
  name: Annotated[str, Field(
    min_length=2,
    max_length=60,
    description="Category name (e.g., 'roof repair contractor', 'community discussion')."
  )]

  confidence: Annotated[float, Field(
    ge=0, le=100,
    description="Confidence score (0–100) estimating how strongly this category applies."
  )]

  reasoning: Annotated[str, Field(
    min_length=5, max_length=160,
    description="One concise sentence explaining the rationale for the categorization."
  )]


class DiscoverCategory(BaseModel):
  items: Annotated[List[Category], Field(
    min_length=5,
    max_length=5,
    description="Exactly five category interpretations ranked by likelihood or relevance."
  )]

  model_config = ConfigDict(
    json_schema_extra={
      "examples": [
        {
          "items": [
            {
              "name": "roofing_repair_service_request",
              "confidence": 94.2,
              "reasoning": "Post asks directly for recommendations for someone to fix a leaking residential roof."
            },
            {
              "name": "storm_damage_home_restoration",
              "confidence": 89.1,
              "reasoning": "Mentions recent storm damage and needing repair quotes, suggesting insurance-related home services."
            },
            {
              "name": "local_contractor_comparison",
              "confidence": 83.7,
              "reasoning": "User compares two named contractors, indicating active decision-making rather than broad browsing."
            },
            {
              "name": "community_reputation_check",
              "confidence": 76.4,
              "reasoning": "Thread tone shows the user is validating trustworthiness rather than negotiating pricing."
            },
            {
              "name": "general_home_maintenance_discussion",
              "confidence": 64.8,
              "reasoning": "Some replies shift toward general advice rather than action-focused contractor engagement."
            }
          ]
        }
      ]
    }
  )
