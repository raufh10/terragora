import json
from collections import defaultdict

path = "data/test.json"

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

if not isinstance(data, list):
    raise ValueError("Expected a list in data/test.json")

total = len(data)
lead_count = sum(1 for d in data if d.get("data", {}).get("is_lead"))
nonlead_count = total - lead_count

label_stats = defaultdict(lambda: {"count": 0, "conf_sum": 0})
confidences = []

for d in data:
    info = d.get("data", {})
    label = info.get("label", "unknown")
    conf = info.get("confidence", 0)
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
