from typing import Optional, Tuple, Dict, Any
from openai import OpenAI
from services.config import credentials

class OpenAIResponse:
  def __init__(
    self,
    default_model: str = "gpt-5-nano-2025-08-07"
  ):
    self.client = OpenAI(api_key=credentials.OPENAI_API_KEY)
    self.model = default_model

  def _build_messages(self, system: Optional[str] = None, user: Optional[str] = None, image: Optional[str] = None) -> list:
    messages = []
    if system:
      messages.append({"role": "system", "content": system})
    if user:
      content = {"role": "user"}
      if image:
        content["content"] = [
          {"type": "text", "text": user},
          {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}}
        ]
      else:
        content["content"] = user
      messages.append(content)
    return messages

  def generate_structured_response(
    self,
    logger,
    system: Optional[str],
    prompt: str,
    response_format: type
  ):
    try:
      response = self.client.beta.chat.completions.parse(
        model=self.model,
        messages=self._build_messages(
          system=system,
          user=prompt
        ),
        response_format=response_format
      )

      return response.choices[0].message.parsed

    except Exception as e:
      logger.error(f"LLM call failed: {e}")
      raise RuntimeError(f"LLM call failed: {e}")