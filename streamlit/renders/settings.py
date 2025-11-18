import streamlit as st
from partials.settings import (
  render_profile,
  render_agenda,
  render_change_password,
  render_delete_account
)

def render_settings():
  st.header("⚙️ Settings")

  render_profile()
  st.divider()

  render_agenda()
  st.divider()

  render_change_password()
  st.divider()

  render_delete_account()
