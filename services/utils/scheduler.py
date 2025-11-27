from datetime import time

DAY_NAME_TO_INDEX = {
  "mon": 0,
  "tue": 1,
  "wed": 2,
  "thu": 3,
  "fri": 4,
  "sat": 5,
  "sun": 6
}

def parse_hms(s: str) -> time:
  parts = s.split(":")
  if not (2 <= len(parts) <= 3):
    raise ValueError(f"Invalid time string: {s!r}")
  hh = int(parts[0]); mm = int(parts[1]); ss = int(parts[2]) if len(parts) == 3 else 0
  return time(hh, mm, ss)
