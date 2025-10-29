from datetime import datetime, timezone
from typing import Iterable, List, Optional, Callable, Dict, Union
import inspect

from scheduler.models import Rule
from services.config import settings

from logger import start_logger
logger = start_logger()

def _normalize_rule_dict(d: Dict[str, Any]) -> Dict[str, Any]:
  if "tr" in d:
    return d
  tr = {
    "start": d.get("start"),
    "end": d.get("end"),
    "days": d.get("days"),
  }
  return {"tr": tr, "action": d.get("action")}

def build_rules(config: Iterable[dict]) -> List[Rule]:
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

def _resolve_action(name: str) -> Optional[Callable]:
  fn = settings.ACTION_REGISTRY.get(name)
  if not fn:
    logger.warning(f"⚠️ No function registered for action '{name}'.")
    return None
  return fn

def _normalize_actions(action_spec: Union[str, List[str]]) -> List[str]:

  if isinstance(action_spec, list):
    return [a.strip() for a in action_spec if a and a.strip()]
  if isinstance(action_spec, str):
    parts = []
    tmp = action_spec.replace(">", " ").replace(",", " ")
    for p in tmp.split():
      if p.strip():
        parts.append(p.strip())
    return parts
  logger.warning(f"⚠️ Unsupported action spec type: {type(action_spec)}; ignoring.")
  return []

def run_actions(action_spec: Union[str, List[str]]) -> None:

  action_names = _normalize_actions(action_spec)
  if not action_names:
    logger.info("ℹ️ No actions to run.")
    return

  logger.info(f"🧩 Running actions in sequence: {', '.join(action_names)}")
  for name in action_names:
    fn = _resolve_action(name)
    if not fn:
      continue
    try:
      sig = inspect.signature(fn)
      if "logger" in sig.parameters:
        logger.info(f"▶️  {name} (with logger)")
        fn(logger=logger)
      else:
        logger.info(f"▶️  {name}")
        fn()
      logger.info(f"✅ {name} completed")
    except Exception as e:
      logger.exception(f"❌ Error while running action '{name}': {e}")

def main():
  now = datetime.now(timezone.utc)
  timestamp_str = now.strftime("%Y-%m-%d %H:%M UTC")
  rules = build_rules(settings.TIME_RULES)

  if getattr(settings, "LIST_RULES", False):
    logger.info("Listing configured rules (UTC):")
    for i, r in enumerate(rules, 1):
      dset = r.tr.days
      days = "all days" if dset is None else ",".join(str(d) for d in sorted(dset))
      logger.info(f"{i:02d}. {r.tr.start}–{r.tr.end} ({days}) → {r.action}")
    return

  match = choose_matching_rule(now, rules)
  if match:
    run_actions(match.action)
  else:
    logger.debug(f"No matching rule for current UTC time window. {timestamp_str}")
    import requests; print(requests.get(f"{settings.API_ENDPOINT}/", timeout=10).status_code)

if __name__ == "__main__":
  main()
