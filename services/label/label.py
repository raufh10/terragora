from typing import Dict, List, Union
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KeywordValue = Union[List[str], Dict[str, List[str]]]

class RedditPostCategorizer:
  """
  Torch-free version using TF-IDF + cosine similarity.

  Decision order:
    1) lead (if score >= thresh_lead)
    2) related (if score >= thresh_related)
    3) max(question-help, discussion), if score >= thresh_qd
    4) general
  """
  def __init__(
    self,
    keyword_map: dict,
    thresh_lead: float = 0.58,
    thresh_related: float = 0.55,
    thresh_qd: float = 0.52,
    ngram_range=(1, 2),
    min_df: int = 1
  ):
    self.keyword_map = keyword_map
    self.thresh_lead = float(thresh_lead)
    self.thresh_related = float(thresh_related)
    self.thresh_qd = float(thresh_qd)
    self.ngram_range = ngram_range
    self.min_df = min_df

  # ---------- classmethod ----------
  @classmethod
  def process_keywords(cls, keyword_map: dict) -> dict:
    def _normalize_list(lst):
      cleaned, seen = [], set()
      for item in lst:
        text = str(item).strip().lower()
        if text and text not in seen:
          cleaned.append(text)
          seen.add(text)
      return cleaned

    processed = {}
    for subreddit, cats in (keyword_map or {}).items():
      processed[subreddit] = {}
      for cat, value in (cats or {}).items():
        if isinstance(value, dict):  # nested (e.g., lead -> {service: [phrases]})
          subdict = {}
          for subcat, kw_list in (value or {}).items():
            subdict[subcat] = _normalize_list(kw_list or [])
          processed[subreddit][cat] = subdict
        elif isinstance(value, list):  # flat lists
          processed[subreddit][cat] = _normalize_list(value or [])
        else:
          processed[subreddit][cat] = []
    return processed

  # ---------- internals ----------
  def _flatten_keywords(self, value: KeywordValue) -> List[str]:
    if isinstance(value, dict):
      out = []
      for phrases in value.values():
        out.extend(phrases or [])
      return out
    return list(value or [])

  def _avg_similarity(self, text: str, phrases: List[str]) -> float:
    if not phrases:
      return 0.0
    # Fit a tiny TF-IDF model on (phrases + text) to keep vocab focused & fast
    corpus = phrases + [text]
    vect = TfidfVectorizer(ngram_range=self.ngram_range, min_df=self.min_df)
    X = vect.fit_transform(corpus)
    post_vec = X[-1]        # last row = text
    kw_vecs = X[:-1]        # all keyword phrases
    # cosine similarities between post and each keyword phrase
    sims = cosine_similarity(post_vec, kw_vecs)[0]
    return float(sims.mean()) if sims.size else 0.0

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
    text_norm = text.strip().lower()

    lead_phrases       = self._flatten_keywords(categories.get("lead", []))
    related_phrases    = self._flatten_keywords(categories.get("related", []))
    qhelp_phrases      = self._flatten_keywords(categories.get("question-help", []))
    discussion_phrases = self._flatten_keywords(categories.get("discussion", []))

    lead_score       = self._avg_similarity(text_norm, lead_phrases)
    related_score    = self._avg_similarity(text_norm, related_phrases)
    qhelp_score      = self._avg_similarity(text_norm, qhelp_phrases)
    discussion_score = self._avg_similarity(text_norm, discussion_phrases)

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
