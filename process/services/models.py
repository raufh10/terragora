from typing import List, Annotated, Optional
from pydantic import BaseModel, Field, ConfigDict

NotesStr = Annotated[str, Field(max_length=500)]

class PriceRange(BaseModel):
  start: Optional[float] = Field(None, description="The fixed price or the lower bound of a range.")
  max: Optional[float] = Field(None, description="The upper bound of a price range if provided.")

class ProductExtraction(BaseModel):
  model_config = ConfigDict(extra='forbid')

  prices: List[PriceRange] = Field(
    default_factory=list, 
    description="List of prices or price ranges extracted (e.g., {'start': 100000, 'max': 150000})."
  )
  notes: NotesStr = Field(
    description="1-3 sentences of additional context regarding condition, location, or bundle details."
  )
