import streamlit as st
from datetime import datetime

from modules import api
from modules.sections.report import render_expanders_only

from datetime import datetime, timezone

def _parse_iso_date(iso_str: str) -> str:

  try:
    if not iso_str:
      return "-"
    s = iso_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    now = datetime.now(timezone.utc)
    diff = now - dt

    days = diff.days
    seconds = diff.seconds

    if days == 0:
      if seconds < 60:
        return "just now"
      elif seconds < 3600:
        return f"{seconds // 60} min ago"
      else:
        return f"{seconds // 3600} hr ago"
    elif days == 1:
      return "yesterday"
    elif days < 7:
      return f"{days} days ago"
    elif days < 30:
      weeks = days // 7
      return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif days < 365:
      months = days // 30
      return f"{months} month{'s' if months > 1 else ''} ago"
    else:
      years = days // 365
      return f"{years} year{'s' if years > 1 else ''} ago"

  except Exception:
    return "-"

def sort_matches(data: list, sort_type: str = "default"):

  def safe_get_created_at(item):
    try:
      return datetime.fromisoformat(item["posts"]["created_at"])
    except Exception:
      return datetime.min

  def safe_get_score(item):
    try:
      return float(item["data"]["quick_fit"]["likely_match_percent"])
    except Exception:
      return 0.0

  if sort_type == "score":
    sorted_data = sorted(data, key=safe_get_score, reverse=True)
  else:
    sorted_data = sorted(data, key=safe_get_created_at, reverse=True)

  return sorted_data

@st.fragment
def render_dashboard(logger):
  try:
    logger.info("🎛️ Rendering user dashboard")

    has_alerts = bool(st.session_state.get("alert_data"))
    logger.debug(f"Alert data detected: {has_alerts}")

    # --- Render Dashboard ---
    if has_alerts:
      profile_data = st.session_state.get("user_profile") or {}
      logger.debug(f"User profile keys: {list(profile_data.keys()) if isinstance(profile_data, dict) else 'N/A'}")

      # -- Initialize Resume ID --
      try:
        resume_id = (profile_data.get("user_resumes") or {}).get("id")
      except Exception:
        resume_id = None

      if not resume_id:
        logger.warning("⚠️ Missing resume_id; re-prompting user to re-identify")
        st.warning("⚠️ We couldn’t locate your resume reference. Please confirm your email again to reload your matches.")

        st.session_state.pop("alert_data", None)
        st.session_state.pop("user_profile", None)
        st.rerun(scope="fragment")

      # -- Initialize Alert Data --
      alert_data = st.session_state.get("alert_data") or []
      logger.info(f"📬 Found {len(alert_data)} alert(s) for resume_id={resume_id}")

      # -- Dashboard Title --
      st.markdown("<h3 style='text-align: center;'>📊 Dashboard</h3>", unsafe_allow_html=True)
      st.divider()

      # -- Alert Data Sorting --
      sort_options = {
        "default": "🕓 Newest",
        "score": "🎯 Best Match",
      }

      sort_type = st.segmented_control(
        "Sort by",
        options=list(sort_options.keys()),
        format_func=lambda opt: sort_options[opt],
        default="default",
        selection_mode="single",
      )
      sorted_data = sort_matches(alert_data, sort_type)

      # -- For Loop Alert Data --
      for idx, item in enumerate(sorted_data):
        try:

          # - Initialize Matches & Post Data -
          logger.debug(f"[{idx}] Processing alert id={item.get('id')}")

          matches_id = item.get("id")
          data = item.get("data") or {}
          score = (data.get("quick_fit") or {}).get("likely_match_percent", "No score available")

          posts = item.get("posts") or {}
          url = posts.get("urls_id")
          created_at = _parse_iso_date(posts.get("created_at"))

          data_raw = posts.get("data_raw") or {}
          title = data_raw.get("job_title", "Untitled role")
          company_name = data_raw.get("company_name", "Unknown company")

          salary = data_raw.get("job_salary_as_string", "")
          if not any(keyword in str(salary) for keyword in ["Rp", "IDR"]) and not any(ch.isdigit() for ch in str(salary)):
            salary = "Salary not listed"

          if not url:
            logger.warning(f"[{idx}] Missing URL — disabling source link.")
          if not matches_id:
            logger.warning(f"[{idx}] Missing matches_id — disabling analysis link.")

          # - Render Matches & Post Data -
          with st.container(
            border=True
          ):
            st.markdown(f"#### **{title}** | {company_name}")

            dc1, dc2 = st.columns(
              [4, 1],
              vertical_alignment="center",
            )

            with dc1:
              st.caption(f"📅 {created_at or 'Date unavailable'}")
              st.write(f"💰 *{salary}*")

            with dc2:
              st.metric("**📊 Score**", score)

            # - Render Links -
            bc1, bc2, bc3 = st.columns(
              [2, 2, 2],
              vertical_alignment="center",
            )

            with bc2:
              if url:
                st.link_button(
                  "Visit Job Post",
                  url,
                  type="primary",
                  icon="🔗",
                  width="stretch"
                )
              else:
                st.button("Source Unavailable", disabled=True)

          render_expanders_only(data, logger)

        except Exception as item_err:
          logger.exception(f"❌ Failed rendering alert item: {item_err}")
          st.warning("⚠️ One of the job matches couldn’t be displayed. We skipped it and continued with the rest.")

    # --- User Authentification ---
    else:
      logger.info("No alerts found; rendering user identification form")

      with st.container(horizontal_alignment="center", vertical_alignment="center"):
        st.markdown("<h3 style='text-align: center;'>👋 Welcome back</h3>", unsafe_allow_html=True)

        ec1, ec2, ec3 = st.columns(3)
        with ec2:

          user_input = st.text_input(
            "Enter your email",
            placeholder="Email address",
            label_visibility="hidden",
            icon="📧"
          )

          if st.button("Continue", type="primary", width="stretch"):

            # -- Checks for User Input --
            if not (user_input or "").strip():
              st.warning("⚠️ Please enter your email before continuing.")
              logger.warning("User submitted empty email input.")

            # -- API Call Analysis & Store Data in Session State --
            else:
              try:
                logger.info(f"🔍 Fetching data for user={user_input}")
                profile, alerts = api.get_analysis(logger, user_input)
                logger.debug(
                  f"get_analysis → profile_keys={list(profile.keys()) if isinstance(profile, dict) else 'N/A'} "
                  f"| alert_count={len(alerts) if isinstance(alerts, list) else 'N/A'}"
                )

                if not profile or not isinstance(alerts, list):
                  logger.warning("Incomplete analysis response; retrying.")

                  try:
                    created_at_str = profile.get("created_at")
                    if created_at_str:
                      created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                      now = datetime.now(timezone.utc)
                      diff_hours = (now - created_at).total_seconds() / 3600

                      if diff_hours < 24:
                        st.info(
                          "👋 Hi there! We’re still processing your first resume match. "
                          "This usually takes a few minutes — please check back shortly. ⏳"
                        )
                        return

                      else:
                        st.info(
                          "ℹ️ No new matches yet. We’ll notify you once new job postings fit your resume. 🔔"
                        )
                        return

                    else:
                      st.info("⚠️ Profile timestamp not found. Please try reloading your dashboard.")
                      return

                  except Exception as e:
                    st.warning(f"⚠️ Could not interpret profile creation time: {e}")

                st.session_state["user_profile"], st.session_state["alert_data"] = profile, alerts
                st.success("✅ Profile loaded successfully! Building your dashboard...")
                st.rerun(scope="fragment")

              except Exception as fetch_err:
                logger.exception(f"🔥 API call failed during get_analysis: {fetch_err}")
                st.error("🚨 We ran into a temporary issue fetching your data. Please try again shortly.")

  except Exception as e:
    logger.exception(f"💥 Unexpected error in render_dashboard: {e}")
    st.error("🚨 Oops! Something went wrong while loading your dashboard. Please refresh or try again later.")
