import streamlit as st
from datetime import datetime, timedelta

PAGE_SIZE = 6

def _mk_item(idx: int, title: str, minutes_ago: int, preview_url: str = "", category: str = "", tags=None):
  dt = datetime.utcnow() - timedelta(minutes=minutes_ago)
  return {
    "id": idx,
    "title": title,
    "preview_url": preview_url,
    "created_human": dt.strftime("%Y-%m-%d %H:%M UTC"),
    "category": category or "uncategorized",
    "tags": tags or [],
    "reddit_url": f"https://reddit.com/r/example/comments/mock_{idx}",
  }

def _mock_items():
  return [
    _mk_item(1,  "Trade Rumor: Big move incoming?", 20,  "", "discussion", ["lakers", "rumor"]),
    _mk_item(2,  "New build advice: 7800X3D vs 9900K", 60, "https://placehold.co/600x300", "services", ["buildapc", "hardware"]),
    _mk_item(3,  "AEW show tonight: predictions?", 90,  "", "discussion", ["aew", "wrestling"]),
    _mk_item(4,  "Ask HN: Best lightweight job tracker?", 120, "", "jobs", ["hackernews", "tools"]),
    _mk_item(5,  "City guide: food near arena?", 180, "", "discussion", ["losangeles", "food"]),
    _mk_item(6,  "Hot take: top shot selection", 240, "", "announcement", ["lakers", "opinion"]),
    _mk_item(7,  "PSA: Hiring data analysts (remote)", 300, "", "jobs", ["forhire", "remote"]),
    _mk_item(8,  "Show & Tell: My CLI Reddit client", 360, "https://placehold.co/500x200", "services", ["python", "cli"]),
    _mk_item(9,  "Match thread: Game night chat", 420, "", "discussion", ["lakers", "gamethread"]),
    _mk_item(10, "New Mod Tool preview", 500, "", "announcement", ["modsupport", "preview"]),
  ]

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
