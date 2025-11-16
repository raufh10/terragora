import streamlit as st
from datetime import datetime
from modules.api import fetch_submissions_feed


PAGE_SIZE = 10  # as used by backend


def _setup_feed_state():
  if "agenda_feed" not in st.session_state:
    st.session_state.agenda_feed = []
  if "feed_page" not in st.session_state:
    st.session_state.feed_page = 1


def _format_timestamp(ts):
  try:
    return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M UTC")
  except:
    return "unknown time"


def feed_controller():
  _setup_feed_state()

  cols = st.columns([1, 0.2])
  with cols[0]:
    st.subheader("Newest posts")
  with cols[1]:
    if st.button("Refresh", key="feed_refresh"):
      st.session_state.feed_page = 1
      st.session_state.agenda_feed = []
      st.rerun()


def feed():
  _setup_feed_state()

  logger = st.session_state.get("logger")
  agenda_id = st.session_state.get("agenda_id")

  if not agenda_id:
    st.warning("No agenda selected. Go to Settings to configure one.")
    return

  page = st.session_state.feed_page

  # ----------------------------
  # Fetch backend feed
  # ----------------------------
  resp = fetch_submissions_feed(logger, agenda_id, page=page, per_page=PAGE_SIZE)

  if not resp.get("ok"):
    st.error(resp.get("error", "Failed to load feed"))
    return

  items = resp.get("data", [])

  # Append to session for pagination consistency
  st.session_state.agenda_feed.extend(items)

  # ----------------------------
  # Render each real item
  # ----------------------------
  for it in items:
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

      # post body (optional)
      if it.get("is_self") and it.get("selftext"):
        with st.expander("Post body"):
          st.write(it["selftext"])

      # Reddit link
      st.link_button("View on Reddit", it.get("url"))

  # ----------------------------
  # Load more button
  # ----------------------------
  if resp.get("count", 0) >= PAGE_SIZE:
    st.divider()
    if st.button("Load more", key=f"more_page_{page}"):
      st.session_state.feed_page += 1
      st.rerun()
