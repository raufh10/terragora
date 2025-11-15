import streamlit as st
from modules.mock import PAGE_SIZE, _mk_item, _mock_items

def _setup_feed_state():
  if "feed_items" not in st.session_state:
    st.session_state.feed_items = _mock_items()
  if "feed_page" not in st.session_state:
    st.session_state.feed_page = 1

def feed_controller():
  _setup_feed_state()
  cols = st.columns([1, 0.2])
  with cols[0]:
    st.subheader("Newest posts")
  with cols[1]:
    if st.button("Refresh", key="feed_refresh"):
      st.session_state.feed_items = _mock_items()  # regenerate mock list
      st.session_state.feed_page = 1
      st.toast("Feed refreshed", icon="✅")

def _paginate(items, page: int):
  start = (page - 1) * PAGE_SIZE
  end = start + PAGE_SIZE
  chunk = items[start:end]
  has_more = end < len(items)
  next_page = page + 1
  return chunk, has_more, next_page

def feed():
  _setup_feed_state()
  items = st.session_state.feed_items
  page = st.session_state.feed_page

  chunk, has_more, next_page = _paginate(items, page)

  st.write(st.session_state["auth_token"])
  for it in chunk:
    with st.container(border=True):
      st.markdown(f"### {it['title']}")
      if it.get("preview_url"):
        st.image(it["preview_url"], use_container_width=True)
      meta_cols = st.columns([0.35, 0.35, 0.3])
      with meta_cols[0]:
        st.caption(it["created_human"])
      with meta_cols[1]:
        st.caption(f"category: {it.get('category', 'uncategorized')}")
      with meta_cols[2]:
        tags = it.get("tags") or []
        if tags:
          st.caption(" · ".join([str(t) for t in tags]))
        else:
          st.caption("no tags")

      st.link_button("View on Reddit", it["reddit_url"])

  if has_more:
    st.divider()
    if st.button("Load more", key=f"feed_more_{page}"):
      st.session_state.feed_page = next_page
      st.rerun()
