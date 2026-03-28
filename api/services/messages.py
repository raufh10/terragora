from typing import List, Optional
from services.llm import MarketplaceSearch

def format_telegram_message(
  user_query: str,
  result: Optional[MarketplaceSearch],
  relevant_posts: List[dict]
) -> str:
  if not result or not result.listings:
    return f"🔍 Terragora Results: {user_query}\n\nNo relevant listings found."

  # Pair listings with posts
  paired = []
  for i, listing in enumerate(result.listings):
    post = relevant_posts[i] if i < len(relevant_posts) else {}
    paired.append((listing, post))

  # Sort by deal_score
  paired.sort(
    key=lambda x: (x[0].deal_score is not None, x[0].deal_score or 0),
    reverse=True
  )

  def format_rp(value):
    if value is None:
      return None
    return f"{int(value):,}".replace(",", ".")

  def format_price(price):
    # Case 1: None
    if not price:
      return "Rp -"

    # Case 2: Single number
    if isinstance(price, (int, float)):
      return f"Rp {format_rp(price)}"

    # Case 3: List of dicts (bundle / multiple items)
    if isinstance(price, list):
      parts = []
      total_min = 0
      total_max = 0
      has_max = False

      for p in price:
        start = p.get("start")
        max_p = p.get("max")

        if start:
          total_min += start
        if max_p:
          total_max += max_p
          has_max = True
        else:
          total_max += start if start else 0

        # Per-item display
        if start and max_p:
          parts.append(f"{format_rp(start)}–{format_rp(max_p)}")
        elif start:
          parts.append(f"{format_rp(start)}")

      # Join individual prices
      price_line = "Rp " + ", ".join(parts)

      # Add total
      if len(price) > 1:
        if has_max:
          total_str = f"{format_rp(total_min)}–{format_rp(total_max)}"
        else:
          total_str = f"{format_rp(total_min)}"

        price_line += f" (Total: Rp {total_str})"

      return price_line

    # Fallback
    return f"Rp {price}"

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
    price = post.get("price")
    url = post.get("metadata", {}).get("url", "#")

    price_str = format_price(price)

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
