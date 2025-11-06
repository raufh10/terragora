from enum import Enum
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict

class LeadLabel(str, Enum):
  # 🏥 Health & Medical Professions
  personal_trainer = "personal_trainer"
  nutrition_coach = "nutrition_coach"
  massage_therapist = "massage_therapist"
  yoga_instructor = "yoga_instructor"
  physical_therapist = "physical_therapist"
  mindfulness_instructor = "mindfulness_instructor"

  # 🚗 Automotive Professions
  auto_mechanic = "auto_mechanic"
  car_detailer = "car_detailer"

  # 🏠 Home Services & Improvement Professions
  landscaper = "landscaper"
  pressure_washing = "pressure_washing"
  electrician = "electrician"
  plumber = "plumber"
  hvac_technician = "hvac_technician"
  flooring_installer = "flooring_installer"
  roofing_specialist = "roofing_specialist"

  # 🏡 Real Estate Professions
  real_estate_agent = "real_estate_agent"

  # 🗣️ Non-lead General Categories
  discussion = "discussion"
  question = "question"
  help = "help"
  other = "other"

class PostCategory(BaseModel):
  is_lead: Annotated[bool, Field(
    description="True if this post represents a potential business lead; False if it’s general or informational."
  )]

  label: Annotated[LeadLabel, Field(
    description=(
      "If is_lead=True, label corresponds to a business/profession category (e.g., 'plumber', 'landscaper'). "
      "If is_lead=False, it corresponds to general discussion types (e.g., 'discussion', 'question')."
    )
  )]

  confidence: Annotated[float, Field(
    ge=0, le=100,
    description="Confidence score (0–100) reflecting certainty in this classification."
  )]

  model_config = ConfigDict(
    json_schema_extra={
      "examples": [
        {"is_lead": True, "label": "plumber", "confidence": 91.8},
        {"is_lead": False, "label": "discussion", "confidence": 78.4}
      ]
    }
  )
