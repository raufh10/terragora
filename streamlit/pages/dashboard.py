import streamlit as st
from partials.dashboard import feed_controller, feed

def render_dashboard():
  with st.container(border=True):
    st.header("📊 Dashboard")
    feed_controller()
    st.divider()
    feed()
