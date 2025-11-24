import streamlit as st
from datetime import datetime
from typing import Optional
from modules.api import fetch_submissions_feed, run_suggest
from modules.config import PAGE_SIZE

# --------------------------
# Internal feed state helper
# --------------------------
def _setup_feed_state():
  if "agenda_feed" not in st.session_state:
    st.session_state.agenda_feed = []
  if "feed_page" not in st.session_state:
    st.session_state.feed_page = 1
  if "feed_sort" not in st.session_state:
    st.session_state.feed_sort = "default"
  if "feed_keyword" not in st.session_state:
    st.session_state.feed_keyword = ""
  if "feed_category" not in st.session_state:
    # store the *selected* category string; "" means "All"
    st.session_state.feed_category = ""


# --------------------------
# Human timestamp formatter
# --------------------------
def _format_timestamp(ts: Optional[float]) -> str:
  try:
    return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M UTC")
  except Exception:
    return "unknown time"


# --------------------------
# Controller (filters + refresh)
# --------------------------
def feed_controller():
  _setup_feed_state()

  top_cols = st.columns([1, 1])
  with top_cols[0]:
    st.subheader("Newest posts")
  with top_cols[1]:
    if st.button("Refresh", key="feed_refresh"):
      # Reset pagination + accumulated items
      st.session_state.feed_page = 1
      st.session_state.agenda_feed = []
      st.rerun()

  # Filter + sort controls
  with st.expander("Filter & sort", expanded=False):
    cols = st.columns(3)

    # --- Sort control ---
    with cols[0]:
      sort_label = st.selectbox(
        "Sort by",
        ["Most recent", "Most comments", "Top scores"],
        index={
          "default": 0,
          "num_comments": 1,
          "scores": 2
        }.get(st.session_state.get("feed_sort", "default"), 0),
      )
      sort_map = {
        "Most recent": "default",
        "Most comments": "num_comments",
        "Top scores": "scores",
      }
      st.session_state.feed_sort = sort_map.get(sort_label, "default")

    # --- Keyword control ---
    with cols[1]:
      st.session_state.feed_keyword = st.text_input(
        "Keyword (optional)",
        value=st.session_state.get("feed_keyword", ""),
      )

    # --- Category control (from agenda_type list) ---
    with cols[2]:
      raw_categories = st.session_state.get("agenda_type") or []
      # Normalize to list
      if isinstance(raw_categories, str):
        raw_categories = [raw_categories]
      elif not isinstance(raw_categories, list):
        raw_categories = []

      # Build options: "All" + specific categories
      options = ["All"] + raw_categories if raw_categories else ["All"]
      current = st.session_state.get("feed_category") or "All"
      if current not in options:
        current = "All"

      selected = st.selectbox(
        "Category",
        options,
        index=options.index(current),
      )

      # Store "" for All (so backend receives None later)
      st.session_state.feed_category = st.session_state.get("agenda_type") if selected == "All" else [selected]


# --------------------------
# Main Feed Renderer
# --------------------------
def feed():
  _setup_feed_state()

  logger = st.session_state.get("logger")
  agenda_id = st.session_state.get("agenda_id")

  if not agenda_id:
    st.warning("No agenda selected. Go to Settings to configure one.")
    return

  page = st.session_state.feed_page
  sort = st.session_state.get("feed_sort", "default")
  keyword = st.session_state.get("feed_keyword") or None
  category = st.session_state.get("feed_category") or None  # "" → None

  # ----------------------------
  # Fetch backend feed
  # ----------------------------
  resp = fetch_submissions_feed(
    logger,
    agenda_id,
    page=page,
    per_page=PAGE_SIZE,
    sort=sort,
    keyword=keyword,
    category=category,
  )

  if not resp.get("ok"):
    st.error(resp.get("error", "Failed to load feed"))
    return

  items = resp.get("data", [])
  count = resp.get("count", 0)

  # Append into state for persistent pagination across pages
  st.session_state.agenda_feed.extend(items)

  # ----------------------------
  # Render each item
  # ----------------------------
  for it in items:
    with st.container(border=True):
      st.markdown(f"### {it.get('title', '(no title)')}")

      # created time
      human_time = _format_timestamp(it.get("created_utc"))

      meta_cols = st.columns([0.33, 0.33, 0.33])
      with meta_cols[0]:
        st.caption(human_time)
      with meta_cols[1]:
        st.caption(f"category: {it.get('category', 'unknown')}")
      with meta_cols[2]:
        flair = it.get("link_flair_text") or "no flair"
        st.caption(f"flair: {flair}")

      # Post body (optional)
      if it.get("is_self") and it.get("selftext"):
        with st.expander("Post body"):
          st.write(it["selftext"])

      # Reddit link
      st.link_button("View on Reddit", it.get("url"))

      # Angles
      angles_data = it.get("angles_data")
      if angles_data:
        with st.expander("Reply Ideas"):
          st.write(angles_data)
      else:
        logger_local = st.session_state.get("logger")
        user_id = st.session_state.get("user_id")
        submission_id = it.get("id")

        def _on_generate_angles(
          _logger=logger_local,
          _user_id=user_id,
          _submission_id=submission_id,
        ):
          run_suggest(_logger, _user_id, _submission_id)

        st.button(
          "Generate Angles",
          key=f"generate_angles_{submission_id}",
          on_click=_on_generate_angles,
        )

  # ----------------------------
  # Pagination
  # ----------------------------
  if count >= PAGE_SIZE:
    st.divider()
    if st.button("Load more", key=f"more_page_{page}"):
      st.session_state.feed_page += 1
      st.rerun()
