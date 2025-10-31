from typing import Dict, List, Union
from sentence_transformers import SentenceTransformer, util
import torch

KeywordValue = Union[List[str], Dict[str, List[str]]]

class RedditPostCategorizer:
  """
  Torch + SentenceTransformers version.

  Decision order:
    1) lead (if score >= thresh_lead)
    2) related (if score >= thresh_related)
    3) max(question-help, discussion), if score >= thresh_qd
    4) general
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
    Defensive normalizer:
      - Ensures each subreddit value is a dict of categories
      - Accepts legacy/list-only shapes and maps them to 'related'
      - Flattens question-help/discussion {light, heavy} -> list
      - Normalizes strings (strip/lower) and deduplicates
      - For 'lead': accepts dict (service->list) OR list; if list, wraps under 'generic'
    """
    def _norm_list(lst):
      out, seen = [], set()
      for x in lst or []:
        s = str(x).strip().lower()
        if s and s not in seen:
          out.append(s)
          seen.add(s)
      return out

    def _flatten_light_heavy(v) -> List[str]:
      if isinstance(v, dict):
        return _norm_list((v.get("light") or []) + (v.get("heavy") or []))
      return _norm_list(v or [])

    if not isinstance(keyword_map, dict):
      # If user passed a top-level list by mistake, coerce to a fake subreddit
      return {"default": {"related": _norm_list(keyword_map)}}

    processed: Dict[str, Dict[str, KeywordValue]] = {}

    for subreddit, cats in (keyword_map or {}).items():
      # If subreddit value is a list, treat it as 'related'
      if isinstance(cats, list):
        processed[subreddit] = {"related": _norm_list(cats)}
        continue

      # If not a dict, coerce to empty dict
      if not isinstance(cats, dict):
        processed[subreddit] = {}
        continue

      out_cats: Dict[str, KeywordValue] = {}

      # --- lead ---
      lead_val = cats.get("lead")
      if isinstance(lead_val, dict):
        out_cats["lead"] = {svc: _norm_list(lst) for svc, lst in (lead_val or {}).items()}
      elif isinstance(lead_val, list):
        out_cats["lead"] = {"generic": _norm_list(lead_val)}
      elif lead_val is not None:
        out_cats["lead"] = {"generic": _norm_list([lead_val])}

      # --- related ---
      rel_val = cats.get("related")
      if rel_val is not None:
        out_cats["related"] = _norm_list(rel_val if isinstance(rel_val, list) else [rel_val])

      # --- question-help ---
      qh_val = cats.get("question-help")
      if qh_val is not None:
        out_cats["question-help"] = _flatten_light_heavy(qh_val)

      # --- discussion ---
      disc_val = cats.get("discussion")
      if disc_val is not None:
        out_cats["discussion"] = _flatten_light_heavy(disc_val)

      processed[subreddit] = out_cats

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
    sims = util.cos_sim(post_emb, kw_emb)  # shape roughly (1, K)
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

    # Decision order & thresholds
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
