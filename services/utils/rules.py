from datetime import datetime
from typing import Iterable, List, Optional, Dict, Any
from scheduler.models import Rule

def _normalize_rule_dict(d: Dict[str, Any]) -> Dict[str, Any]:
  if "start" in d and "end" in d:
    return d
  if "tr" in d and isinstance(d["tr"], dict):
    tr = d["tr"]
    return {
      "start": tr.get("start"),
      "end": tr.get("end"),
      "days": tr.get("days"),
      "action": d.get("action"),
    }
  raise ValueError("Rule must contain 'start'/'end' or 'tr' with those fields")

def build_rules(config: Iterable[dict], logger) -> List[Rule]:
  rules: List[Rule] = []
  for raw in config:
    try:
      norm = _normalize_rule_dict(raw)
      rules.append(Rule.from_dict(norm))
    except Exception as e:
      logger.exception(f"Invalid rule skipped: {raw} | {e}")
  return rules

def choose_matching_rule(now_utc: datetime, rules: List[Rule]) -> Optional[Rule]:
  for r in rules:
    if r.tr.contains(now_utc):
      return r
  return None
