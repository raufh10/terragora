from pydantic import BaseModel, Field
from typing_extensions import Annotated
from typing import List

class Comment(BaseModel):
  text: Annotated[str, Field(
    min_length=1,
    strip_whitespace=True,
    description="One concise, natural Reddit reply idea tailored to the post/subreddit."
  )]

class AlertData(BaseModel):
  relevance: Annotated[float, Field(
    ge=0,
    le=100,
    description=(
      "A numeric relevance score (0–100) indicating how closely the Reddit post "
      "matches the intent described in the agenda prompt. Higher means stronger relevance."
    )
  )]

  suggestions: Annotated[List[Comment], Field(
    min_length=5,
    max_length=5,
    description="Exactly five comment ideas to consider replying with on the Reddit post."
  )]
