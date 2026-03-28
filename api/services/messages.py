from typing import List, Optional
from services.llm import MarketplaceSearch

def format_telegram_message(
  user_query: str,
  result: Optional[MarketplaceSearch],
  relevant_posts: List[dict]
) -> str:
  if not result or not result.listings:
    return f"🔍 Terragora Results: {user_query}\n\nNo relevant listings found."

  paired = []
  for i, listing in enumerate(result.listings):
    post = relevant_posts[i] if i < len(relevant_posts) else {}
    paired.append((listing, post))

  paired.sort(
    key=lambda x: (x[0].deal_score is not None, x[0].deal_score or 0),
    reverse=True
  )

  lines = []

  # Header
  total = len(paired)
  lines.append(f"🔍 Terragora Results: {user_query}")
  lines.append(f"📊 Found: {total} listings | Sorted by: Best Value")
  lines.append("")
  lines.append("━━━━━━━━━━━━━━━")
  lines.append("")

  # Listings
  for i, (listing, post) in enumerate(paired):
    title = post.get("title", "Unknown Item")
    price = post.get("price", "N/A")
    url = post.get("metadata", {}).get("url", "#")

    # Normalize price
    if isinstance(price, (int, float)):
      price_str = f"Rp {int(price):,}".replace(",", ".")
    else:
      price_str = f"Rp {price}"

    lines.append(f"{i+1}. {title}")
    lines.append("")
    lines.append(f"💰 Price: {price_str}")

    if listing.location:
      lines.append(f"📍 Location: {listing.location}")

    lines.append(f"📦 Condition: {listing.condition}")

    if listing.deal_score is not None:
      lines.append(f"📈 Deal Score: {listing.deal_score}/10")

    lines.append("")
    lines.append("📝 Seller Notes:")
    for note in listing.seller_notes:
      lines.append(f"• {note}")

    lines.append("")
    lines.append(f"✅ Verdict: {listing.verdict}")
    lines.append(f"⚠️ Watch Out: {listing.watch_out or '-'}")
    lines.append("")
    lines.append(f"🔗 View Post: {url}")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━")
    lines.append("")

  return "\n".join(lines).strip()
