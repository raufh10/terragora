from typing import List, Annotated
from pydantic import BaseModel, Field, ConfigDict

NotesStr = Annotated[str, Field(max_length=500)]

class ProductExtraction(BaseModel):
  model_config = ConfigDict(extra='forbid')

  prices: List[float] = Field(
    default_factory=list, 
    description="Numerical prices extracted from the text."
  )
  notes: NotesStr = Field(
    description="1-3 sentences of additional context regarding condition, location, or bundle details."
  )
