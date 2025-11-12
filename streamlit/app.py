import streamlit as st
from modules import DashboardSessionStateBuilder
from modules.utils.queries import check_query_params
from modules.sections.dashboard import render_dashboard

from logger import start_logger
logger = start_logger()

st.set_page_config(
  page_title="Solidfit | Job Seeker's Assistant",
  page_icon="🧩",
  layout="wide",
  initial_sidebar_state="expanded"
)

if __name__ == "__main__":
  try:

    qp = st.query_params
    if qp:

      logger.info(f"🏁 App start | has query parameter")
      check_query_params(qp, logger)

    else:
      logger.info("🧭 No task in query params; loading main flow")
      session = DashboardSessionStateBuilder(logger)

      try:
        session.build()
        logger.debug("Session state built successfully")
      except Exception as e:
        logger.exception(f"❌ DashboardSessionStateBuilder.build() failed: {e}")

      render_dashboard(logger)

  except Exception as e:
    logger.critical(f"🛑 Critical failure at app entrypoint: {e}", exc_info=True)
    st.error("A critical error occurred while starting the app.")
