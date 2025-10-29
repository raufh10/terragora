from pydantic import BaseModel, Field
from typing_extensions import Annotated

class AlertData(BaseModel):
  relevance: Annotated[float, Field(ge=0, le=100)] = Field(
    description=(
      "A numeric relevance score (0–100) indicating how closely the Reddit post "
      "matches the intent described in the agenda prompt. "
      "Higher values mean stronger relevance between the post content and the target topic. "
      "For example, a post directly discussing the requested topic may score above 80, "
      "while off-topic posts should score near 0."
    )
  )

  """
  message: Annotated[str, Field(min_length=1, strip_whitespace=True)] = Field(
    description=(
      "A concise and natural Reddit reply that aligns with the post context and the target subreddit. "
      "The message should read as if written by a real user contributing meaningfully to the discussion. "
      "It can include insights, advice, experiences, or friendly remarks, depending on the subreddit tone. "
      "Avoid generic or spammy phrasing — the goal is to encourage upvotes and engagement while staying relevant."
    )
  )
 """
