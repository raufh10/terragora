import asyncio
from collections import defaultdict
from services.database import db, submissions

from logger import start_logger
logger = start_logger()

def print_overview(data):
  if not isinstance(data, list):
    raise ValueError("Expected a list")

  total = len(data)
  lead_count = sum(1 for d in data if d.get("test_data", {}).get("is_lead"))
  nonlead_count = total - lead_count

  label_stats = defaultdict(lambda: {"count": 0, "conf_sum": 0})
  confidences = []

  for d in data:
    info = d.get("test_data", {}) or {}
    label = info.get("label", "unknown")
    conf = float(info.get("confidence", 0))
    label_stats[label]["count"] += 1
    label_stats[label]["conf_sum"] += conf
    confidences.append(conf)

  # --- Print results ---
  print(f"📊 Total posts: {total}")
  print(f"✅ Leads: {lead_count} | 💬 Non-leads: {nonlead_count}")

  print("\n🏷️ Label stats:")
  for label, stat in label_stats.items():
    avg_conf = stat["conf_sum"] / stat["count"]
    print(f"  - {label}: {stat['count']} posts | avg_conf={avg_conf:.2f}")

  overall_avg = sum(confidences) / len(confidences) if confidences else 0
  print(f"\n📈 Overall avg confidence: {overall_avg:.2f}")

  # Simple distribution buckets
  buckets = {"0–50": 0, "50–70": 0, "70–90": 0, "90–100": 0}
  for c in confidences:
    if c < 50: buckets["0–50"] += 1
    elif c < 70: buckets["50–70"] += 1
    elif c < 90: buckets["70–90"] += 1
    else: buckets["90–100"] += 1

  print("\n📊 Confidence distribution:")
  for rng, count in buckets.items():
    pct = (count / total * 100) if total else 0
    print(f"  {rng}: {count} ({pct:.1f}%)")

def print_label(data, label: str):

  label = label.lower()
  filtered = [
    d.get("test_data") for d in data
    if isinstance(d.get("test_data"), dict)
    and str(d.get("test_data", {}).get("label", "")).lower() == label
  ]

  if not filtered:
    print(f"⚠️ No posts found with label '{label}'")
    return

  confs = [float(d.get("confidence", 0)) for d in filtered]
  avg_conf = sum(confs) / len(confs)

  print(f"\n🎯 Label: {label}")
  print(f"  Count: {len(filtered)}")
  print(f"  Avg confidence: {avg_conf:.2f}")

if __name__ == "__main__":
  data = asyncio.run(submissions.select(db.get_supabase_client(), logger, "Rochester"))

  #print_overview(data)
  print_label(data, "real_estate_agent")
