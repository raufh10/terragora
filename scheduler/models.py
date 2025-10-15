from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional, Set
from .utils import parse_hms, DAY_NAME_TO_INDEX

@dataclass(frozen=True)
class TimeRange:
  start: time
  end: time
  days: Optional[Set[int]] = field(default=None)

  def matches_day(self, dt: datetime) -> bool:
    if self.days is None:
      return True
    return dt.weekday() in self.days

  def contains_time(self, t: time) -> bool:
    if self.start <= self.end:
      return self.start <= t < self.end
    else:
      return t >= self.start or t < self.end

  def contains(self, dt: datetime) -> bool:
    return self.matches_day(dt) and self.contains_time(dt.time())

@dataclass(frozen=True)
class Rule:
  tr: TimeRange
  action: str

  @staticmethod
  def from_dict(d: dict) -> "Rule":
    start = parse_hms(d["start"])
    end = parse_hms(d["end"])
    days_raw = d.get("days")
    if days_raw is None:
      days = None
    else:
      normalized: Set[int] = set()
      for item in days_raw:
        if isinstance(item, int):
          if 0 <= item <= 6:
            normalized.add(item)
          else:
            raise ValueError(f"Weekday index out of range 0-6: {item}")
        else:
          key = str(item).strip().lower()[:3]
          if key not in DAY_NAME_TO_INDEX:
            raise ValueError(f"Unknown day specifier: {item!r}")
          normalized.add(DAY_NAME_TO_INDEX[key])
      days = normalized
    return Rule(tr=TimeRange(start=start, end=end, days=days), action=d["action"])
