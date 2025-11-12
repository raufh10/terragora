import streamlit as st

def render_submit(logger):
  try:
    st.markdown("<h2 style='text-align: center;'>Submission Result</h2>", unsafe_allow_html=True)
    submit = st.session_state.get("submit")
    if submit:
      logger.info("🎉 Submission successful.")
      st.markdown(
        """
        <div style="text-align: center; font-size: 80px; color: green;">
          ✅
        </div>
        <h3 style="text-align: center; color: black;">
          Congratulations! Your details have been submitted successfully.
        </h3>
        """,
        unsafe_allow_html=True
      )
    else:
      logger.warning("❌ Submission failed.")
      st.markdown(
        """
        <div style="text-align: center; font-size: 80px; color: red;">
          ❌
        </div>
        <h3 style="text-align: center; color: black;">
          Submission Failed. Something went wrong on our end. Please try submitting again in a moment.
        </h3>
        """,
        unsafe_allow_html=True
      )
      st.info(
        "📧 If the issue persists, contact us at **rauf@solidfit.online**",
        icon="ℹ️"
      )
  except Exception as e:
    logger.error(f"Error in render_submit: {e}")
    st.error("An error occurred while displaying the submission result.")