# pages/home.py
import streamlit as st
from pages.dashboard import render_dashboard

def render_home():
  st.header("🚀 Build, Track & Act — Faster")

  st.write(
    """
    A lightweight FastAPI + HTMX + Alpine starter for dashboards, feeds, and account settings.  
    **Server-rendered, snappy interactions, and production-ready.**
    """
  )

  col1, col2 = st.columns(2)

  with col1:
    if st.button("Create Account"):
      st.info("Navigate to /account (mock).")

  with col2:
    if st.button("Live Demo (modal-style preview)"):
      with st.expander("📊 Live Demo Preview", expanded=True):
        render_dashboard()

  st.divider()
  st.subheader("Why you'll love it")

  feat_cols = st.columns(4)
  with feat_cols[0]:
    st.markdown("### ⚡ HTMX Interactions")
    st.caption("Fast partial updates with no SPA complexity.")
  with feat_cols[1]:
    st.markdown("### 🧩 Jinja2 Templates")
    st.caption("Composable, maintainable UI structure.")
  with feat_cols[2]:
    st.markdown("### 🪶 Alpine.js Micro-UX")
    st.caption("Small, targeted interactivity — zero bloat.")
  with feat_cols[3]:
    st.markdown("### 🔒 Ready for Auth")
    st.caption("Drop-in login, sign-up, and settings flows.")

  st.divider()
  st.subheader("Q & A")

  with st.expander("How do I deploy?"):
    st.caption(
      "Deploy on Railway with the included Dockerfile — Railway automatically provides your `PORT`."
    )

  with st.expander("Can I customize the UI?"):
    st.caption("Yes — templates and components are intentionally simple.")

  with st.expander("Is there a live demo?"):
    st.caption("Yep — use the **Live Demo** button above.")
