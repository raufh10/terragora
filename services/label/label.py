from sentence_transformers import SentenceTransformer, util
import torch
from typing import Dict, List, Union

KeywordValue = Union[List[str], Dict[str, List[str]]]

class RedditPostCategorizer:
  """
  Decision order:
    1️⃣ lead (if score >= thresh_lead)
    2️⃣ related (if score >= thresh_related)
    3️⃣ max(question-help, discussion), if score >= thresh_qd
    4️⃣ general
  """
  def __init__(
    self,
    keyword_map: dict,
    model_name: str = "all-MiniLM-L6-v2",
    thresh_lead: float = 0.58,
    thresh_related: float = 0.55,
    thresh_qd: float = 0.52,
  ):
    self.keyword_map = keyword_map
    self.model = SentenceTransformer(model_name)
    self.thresh_lead = float(thresh_lead)
    self.thresh_related = float(thresh_related)
    self.thresh_qd = float(thresh_qd)

  # ---------- classmethod ----------
  @classmethod
  def process_keywords(cls, keyword_map: dict) -> dict:
    """
    Normalize, lowercase, and deduplicate keywords in-place.
    Also flattens nested structures for consistency.
    """
    def _normalize_list(lst):
      cleaned = []
      seen = set()
      for item in lst:
        text = item.strip().lower()
        if text and text not in seen:
          cleaned.append(text)
          seen.add(text)
      return cleaned

    processed = {}
    for subreddit, cats in keyword_map.items():
      processed[subreddit] = {}
      for cat, value in cats.items():
        if isinstance(value, dict):  # nested (e.g., lead)
          subdict = {}
          for subcat, kw_list in value.items():
            subdict[subcat] = _normalize_list(kw_list)
          processed[subreddit][cat] = subdict
        elif isinstance(value, list):  # flat (related, question-help, discussion)
          processed[subreddit][cat] = _normalize_list(value)
        else:
          processed[subreddit][cat] = []
    return processed

  # ---------- internals ----------
  def _encode(self, texts: Union[str, List[str]]):
    if isinstance(texts, str):
      texts = [texts]
    return self.model.encode(texts, convert_to_tensor=True)

  def _flatten_keywords(self, value: KeywordValue) -> List[str]:
    if isinstance(value, dict):
      out = []
      for phrases in value.values():
        out.extend(phrases or [])
      return out
    return list(value or [])

  def _avg_similarity(self, post_emb, phrases: List[str]) -> float:
    if not phrases:
      return 0.0
    kw_emb = self._encode(phrases)
    sims = util.cos_sim(post_emb, kw_emb)
    return float(torch.mean(sims))

  # ---------- public API ----------
  def categorize_post(self, subreddit: str, text: str):
    """
    Returns:
      {
        "category": "lead|related|question-help|discussion|general",
        "score": float,
        "scores": { "lead": x, "related": y, "question-help": z, "discussion": w }
      }
    """
    if not text or not subreddit:
      return {"category": "general", "score": 0.0, "scores": {}}

    categories: Dict[str, KeywordValue] = self.keyword_map.get(subreddit, {})
    post_emb = self._encode(text)

    lead_phrases       = self._flatten_keywords(categories.get("lead", []))
    related_phrases    = self._flatten_keywords(categories.get("related", []))
    qhelp_phrases      = self._flatten_keywords(categories.get("question-help", []))
    discussion_phrases = self._flatten_keywords(categories.get("discussion", []))

    lead_score       = self._avg_similarity(post_emb, lead_phrases)
    related_score    = self._avg_similarity(post_emb, related_phrases)
    qhelp_score      = self._avg_similarity(post_emb, qhelp_phrases)
    discussion_score = self._avg_similarity(post_emb, discussion_phrases)

    scores = {
      "lead": round(lead_score, 4),
      "related": round(related_score, 4),
      "question-help": round(qhelp_score, 4),
      "discussion": round(discussion_score, 4),
    }

    # --- Decision order & thresholds ---
    if lead_score >= self.thresh_lead:
      return {"category": "lead", "score": round(lead_score, 4), "scores": scores}

    if related_score >= self.thresh_related:
      return {"category": "related", "score": round(related_score, 4), "scores": scores}

    if max(qhelp_score, discussion_score) >= self.thresh_qd:
      if qhelp_score >= discussion_score:
        return {"category": "question-help", "score": round(qhelp_score, 4), "scores": scores}
      else:
        return {"category": "discussion", "score": round(discussion_score, 4), "scores": scores}

    return {"category": "general", "score": 0.0, "scores": scores}
