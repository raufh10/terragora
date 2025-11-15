import streamlit as st
from modules import SessionStateBuilder, PageSetter, run_page_flow

from logger import start_logger
logger = start_logger()

st.title("🧪 Partial Renderer Test")

# --- Session initialization logic ---
if "initiated" not in st.session_state:
  builder = SessionStateBuilder(logger)
  builder.build()
else:
  logger.info("➡️ Session state already exists. Skipping builder.")

pages = PageSetter.get_pages()
pg = st.navigation(pages)
pg.run()

# --- Run unified flow ---
run_page_flow()
