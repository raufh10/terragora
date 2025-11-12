import streamlit as st
from modules import api
from modules import SessionStateBuilder
from modules.sections.report import  ReportPageBuilder

from modules.sections import (
  render_resume_tab,
  render_confirmation,
  render_submit,
  render_test
)

@st.fragment
def main_container(logger):
  try:
    logger.info("🖼️ Rendering main_container")

    mode = st.session_state.get("mode", "upload_resume")
    logger.debug(f"Current mode: {mode}")

    if mode == "upload_resume":
      render_resume_tab(logger)
      resume_txt = st.session_state.get("resume")
      profile = st.session_state.get("user_profile") or {}
      logger.debug(f"Resume present={bool(resume_txt)} | Profile keys={list(profile.keys()) if isinstance(profile, dict) else 'N/A'}")
      if resume_txt and isinstance(profile, dict) and profile:
        logger.info("➡️ Switching mode to 'confirmation'")
        st.session_state["mode"] = "confirmation"
        st.rerun(scope="fragment")

    elif mode == "confirmation":
      render_confirmation(logger)
      confirmation = st.session_state.get("confirmation")
      logger.debug(f"Confirmation keys={list(confirmation.keys()) if isinstance(confirmation, dict) else 'N/A'}")
      if isinstance(confirmation, dict) and confirmation:
        logger.info("➡️ Switching mode to 'submit'")
        st.session_state["mode"] = "submit"
        st.rerun(scope="fragment")

    elif mode == "submit":
      render_submit(logger)

    else:
      logger.warning(f"⚠️ Unknown mode encountered: {mode}")

  except Exception as e:
    logger.exception(f"Error in main_container: {e}")
    st.error(f"An error occurred while rendering Joblit. {e}")

def check_query_params(qp, logger):
  
  if "signup" in qp:
    init_signup(qp, logger)
  elif "analysis" in qp:
    init_report(qp, logger)
  elif "test" in qp:
    init_test(qp, logger)
  else:
    st.error("Unsupported parameters detected")

def init_signup(qp, logger):
  logger.debug(f"Query params | Initialize Sign-Up main container")
  session = SessionStateBuilder(logger)

  try:
    session.build()
    logger.debug("Session state built successfully")
  except Exception as e:
    logger.exception(f"❌ SessionStateBuilder.build() failed: {e}")

  main_container(logger)

def init_report(qp, logger):
  analysis = qp.get("analysis")
  resume_id, matches_id = analysis.split("-")
  logger.debug(f"Query params | id={matches_id} resume_id={resume_id}")

  if resume_id and matches_id:
    try:
      logger.info("📄 Rendering report page via ReportPageBuilder.show()")
      analysis = api.get_single_analysis(logger, resume_id, matches_id)
      ReportPageBuilder.show(logger, analysis["data"])
    except Exception as e:
      logger.exception(f"❌ Failed to render report page: {e}")
      ReportPageBuilder.show(logger, None)
  else:
    logger.warning("⚠️ 'task' present but missing 'id'; showing empty report page")
    ReportPageBuilder.show(logger, None)

def init_test(qp, logger):
  test_code = qp.get("test")
  logger.debug(f"🔍 init_test() triggered | raw_query={qp}")

  if test_code == "password_test123":
    try:
      logger.info("🧪 Test mode activated — running render_test()")
      render_test(logger)
    except Exception as e:
      logger.exception(f"❌ Exception during render_test(): {e}")
  else:
    logger.warning("⚠️ Invalid or missing test code; skipping render_test()")
