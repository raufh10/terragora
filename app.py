from datetime import datetime, timezone
from services.config import settings
from services.utils import (
  build_rules,
  choose_matching_rule,
  run_actions
)

from logger import start_logger
logger = start_logger()

# ---------- Main ----------

def main():
  now = datetime.now(timezone.utc)
  timestamp_str = now.strftime("%Y-%m-%d %H:%M UTC")
  rules = build_rules(settings.TIME_RULES, logger)

  if getattr(settings, "LIST_RULES", False):
    logger.info("Listing configured rules (UTC):")
    for i, r in enumerate(rules, 1):
      dset = r.tr.days
      days = "all days" if dset is None else ",".join(str(d) for d in sorted(dset))
      logger.info(f"{i:02d}. {r.tr.start}–{r.tr.end} ({days}) → {r.action}")
    return

  match = choose_matching_rule(now, rules)
  if match:
    run_actions(match.action, logger)
  else:
    logger.debug(f"No matching rule for current UTC time window. {timestamp_str}")
    import requests; print(requests.get(f"{settings.API_ENDPOINT}/", timeout=10).status_code)

if __name__ == "__main__":
  main()
