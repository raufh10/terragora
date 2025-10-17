from datetime import datetime, timezone
from typing import Iterable, List, Optional
import inspect

from scheduler.models import Rule
from services.config import settings

from logger import start_logger
logger = start_logger()

def build_rules(config: Iterable[dict]) -> List[Rule]:
  return [Rule.from_dict(d) for d in config]

def choose_matching_rule(now_utc: datetime, rules: List[Rule]) -> Optional[Rule]:
  for r in rules:
    if r.tr.contains(now_utc):
      return r
  return None

def run_action(action_name: str) -> None:
  fn = settings.ACTION_REGISTRY.get(action_name)
  if not fn:
    logger.warning(f"⚠️ No function registered for action '{action_name}'.")
    return

  try:
    sig = inspect.signature(fn)
    if "logger" in sig.parameters:
      logger.info(f"🧩 Running action '{action_name}' with logger")
      fn(logger=logger)
    else:
      logger.info(f"🧩 Running action '{action_name}'")
      fn()
  except Exception as e:
    logger.exception(f"❌ Error while running action '{action_name}': {e}")

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
    run_action(match.action)
  else:
    logger.debug(f"No matching rule for current UTC time window. {timestamp_str}")
    import requests; print(requests.get("http://leaddits-api.railway.internal/", timeout=10).status_code)

if __name__ == "__main__":
  main()
