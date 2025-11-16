import streamlit as st
from datetime import datetime
from modules.api import fetch_submissions_feed
from modules.config import PAGE_SIZE

# --------------------------
# Internal feed state helper
# --------------------------
def _setup_feed_state():
  st.write("🛠️ _setup_feed_state() called")

  if "agenda_feed" not in st.session_state:
    st.session_state.agenda_feed = []
    st.write("➡️ Initialized st.session_state.agenda_feed = []")
  else:
    st.write("↪️ agenda_feed already exists, len =", len(st.session_state.agenda_feed))

  if "feed_page" not in st.session_state:
    st.session_state.feed_page = 1
    st.write("➡️ Initialized feed_page = 1")
  else:
    st.write("↪️ feed_page already exists =", st.session_state.feed_page)


# --------------------------
# Human timestamp formatter
# --------------------------
def _format_timestamp(ts):
  st.write("🕒 Formatting timestamp:", ts)
  try:
    formatted = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M UTC")
    st.write("➡️ formatted =", formatted)
    return formatted
  except Exception as e:
    st.write("⚠️ Failed to format timestamp:", e)
    return "unknown time"


# --------------------------
# Controller
# --------------------------
def feed_controller():
  st.write("🧪 feed_controller() started")
  _setup_feed_state()

  cols = st.columns([1, 0.2])
  with cols[0]:
    st.subheader("Newest posts")
  with cols[1]:
    if st.button("Refresh", key="feed_refresh"):
      st.write("🔄 Refresh clicked — resetting feed + page")
      st.session_state.feed_page = 1
      st.session_state.agenda_feed = []
      st.rerun()


# --------------------------
# Main Feed Renderer
# --------------------------
def feed():
  st.write("🧪 feed() started")
  _setup_feed_state()

  logger = st.session_state.get("logger")
  st.write("📝 logger exists:", bool(logger))

  agenda_id = st.session_state.get("agenda_id")
  st.write("📌 agenda_id =", agenda_id)

  if not agenda_id:
    st.warning("⚠️ No agenda selected. Go to Settings to configure one.")
    return

  page = st.session_state.feed_page
  st.write("📄 Current feed page =", page)

  # ----------------------------
  # Fetch backend feed
  # ----------------------------
  st.write("➡️ Calling fetch_submissions_feed() with arguments:")
  st.write("   agenda_id =", agenda_id)
  st.write("   page =", page)
  st.write("   per_page =", PAGE_SIZE)

  resp = fetch_submissions_feed(logger, agenda_id, page=page, per_page=PAGE_SIZE)

  st.write("📬 Raw fetch_submissions_feed response:", resp)

  if not resp.get("ok"):
    st.error(resp.get("error", "Failed to load feed"))
    return

  items = resp.get("data", [])
  count = resp.get("count", 0)

  st.write(f"📦 Received {len(items)} items for this page (count={count})")

  # Append into state for persistent pagination
  before_len = len(st.session_state.agenda_feed)
  st.session_state.agenda_feed.extend(items)
  after_len = len(st.session_state.agenda_feed)

  st.write(f"🧩 agenda_feed length before={before_len}, after={after_len}")

  # ----------------------------
  # Render each item
  # ----------------------------
  for idx, it in enumerate(items, start=1):
    st.write(f"🔹 Rendering item #{idx}:", it)

    with st.container(border=True):
      st.markdown(f"### {it['title']}")

      # created time
      human_time = _format_timestamp(it.get("created_utc"))

      meta_cols = st.columns([0.33, 0.33, 0.33])
      with meta_cols[0]:
        st.caption(human_time)
      with meta_cols[1]:
        st.caption(f"category: {it.get('category','unknown')}")
      with meta_cols[2]:
        flair = it.get("link_flair_text") or "no flair"
        st.caption(f"flair: {flair}")

      # Post body (optional)
      if it.get("is_self") and it.get("selftext"):
        st.write("📝 This item contains selftext → showing expander")
        with st.expander("Post body"):
          st.write(it["selftext"])
      else:
        st.write("ℹ️ No selftext for this post")

      # Reddit link
      st.write("🔗 Reddit URL:", it.get("url"))
      st.link_button("View on Reddit", it.get("url"))

  # ----------------------------
  # Pagination
  # ----------------------------
  if resp.get("count", 0) >= PAGE_SIZE:
    st.divider()
    st.write("📨 Showing load more button (more pages available)")
    if st.button("Load more", key=f"more_page_{page}"):
      st.write("➡️ Load more clicked — advancing page")
      st.session_state.feed_page += 1
      st.rerun()
  else:
    st.write("📭 No more items to load (end of feed)")
