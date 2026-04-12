def format_price(price) -> str:
  def format_rp(value):
    if value is None:
      return None
    return f"{int(value):,}".replace(",", ".")

  if not price:
    return "Rp -"

  # Ensure price is a list of dicts
  if not isinstance(price, list):
    price = [{"start": price}]

  parts = []
  total_min = 0
  total_max = 0
  has_max = False

  for p in price:
    start = p.get("start")
    max_p = p.get("max")

    # Skip items with neither start nor max
    if start is None and max_p is None:
      continue

    # Update totals
    if start is not None:
      total_min += start
    if max_p is not None:
      total_max += max_p
      has_max = True
    else:
      total_max += start if start is not None else 0

    # Per-item display
    if start is not None and max_p is not None:
      parts.append(f"{format_rp(start)}–{format_rp(max_p)}")
    elif start is not None:
      parts.append(f"{format_rp(start)}")
    elif max_p is not None:
      parts.append(f"{format_rp(max_p)}")

  # Join individual prices
  if not parts:
    return "Rp -"

  price_line = "Rp " + ", ".join(parts)

  # Add total if multiple items
  if len(price) > 1:
    if has_max:
      total_str = f"{format_rp(total_min)}–{format_rp(total_max)}"
    else:
      total_str = f"{format_rp(total_min)}"
    price_line += f" (Total: Rp {total_str})"

  return price_line
