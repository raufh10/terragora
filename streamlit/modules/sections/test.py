import streamlit as st
from modules import api

def render_test(logger):
  try:
    logger.info("🧪 Rendering report page placeholder via render_test()")
    st.markdown("<h2 style='text-align: center;'>🧪 Test Report Page</h2>", unsafe_allow_html=True)

    # --- Section 1: Change Email ---
    st.divider()
    st.markdown("### 📧 Change Email")
    st.write("Update your registered email address below:")
    new_email = st.text_input("Enter new email address", placeholder="you@example.com", key="test_email")
    cols = st.columns([1, 1])
    with cols[0]:
      if st.button("Save Email", type="primary", key="btn_save_email"):
        if not new_email:
          st.warning("Please enter an email.")
        else:
          ok = api.update_email_api(logger, new_email)
          st.success("✅ Email updated.") if ok else st.error("❌ Email update failed. See logs.")
    with cols[1]:
      if new_email:
        st.write(f"🖊️ Input detected: **{new_email}**")
      else:
        st.info("✏️ Please enter your new email above to continue.")

    # --- Section 2: Change Password ---
    st.divider()
    st.markdown("### 🔒 Change Password")
    st.write("Update your account password below:")
    new_password = st.text_input("Enter new password", type="password", placeholder="••••••••", key="test_password")
    if st.button("Save Password", type="primary", key="btn_save_password"):
      if not new_password:
        st.warning("Please enter a password.")
      else:
        ok = api.update_password_api(logger, new_password)
        st.success("✅ Password updated.") if ok else st.error("❌ Password update failed. See logs.")

    # --- Section 3: Delete Account ---
    st.divider()
    st.markdown("### 🗑️ Delete Account")
    st.write("Permanently delete your account and all associated data. This action cannot be undone.")
    if st.button("Delete My Account", type="primary", key="btn_delete_account"):
      ok = api.delete_account_api(logger)
      st.error("🚨 Account deletion requested.") if ok else st.error("❌ Delete failed. See logs.")

    # --- Section 4: Upgrade Subscription ---
    st.divider()
    st.markdown("### 💎 Upgrade Subscription")
    st.write("Unlock premium features and advanced analytics by upgrading your plan.")
    plans = {"Pro (Plan 2)": 2, "Premium (Plan 3)": 3}
    chosen_plan = st.selectbox("Select a plan", list(plans.keys()), index=0, key="test_plan")
    if st.button("Upgrade to Selected Plan", type="primary", key="btn_upgrade"):
      ok = api.upgrade_subscription_api(logger, plans[chosen_plan])
      st.success("✨ Upgrade flow initiated.") if ok else st.error("❌ Upgrade failed. See logs.")

    # --- Section 5: Cancel Subscription ---
    st.divider()
    st.markdown("### ❌ Cancel Subscription")
    st.write("Stop your current subscription and revert to the free plan. You’ll keep access until your billing period ends.")
    if st.button("Cancel My Subscription", type="primary", key="btn_cancel_sub"):
      ok = api.cancel_subscription_api(logger)
      st.warning("❌ Subscription cancellation requested.") if ok else st.error("❌ Cancel failed. See logs.")

    # --- Section 6: Preferences ---
    st.divider()
    st.markdown("### ⚙️ Preferences")
    st.write("Set your job search preferences below.")

    # Subsection: Job Roles
    st.markdown("#### 🎯 Job Roles")
    job_roles_options = ["Data Analyst", "Data Engineer", "Machine Learning Engineer"]
    selected_job_roles = st.multiselect("Select preferred roles", job_roles_options, default=[], key="test_roles")

    # Subsection: Locations
    st.markdown("#### 📍 Locations")
    provinces = [
      "All Indonesia","Aceh","Bali","Banten","Bengkulu","DI Yogyakarta","DKI Jakarta","Gorontalo","Jambi",
      "Jawa Barat","Jawa Tengah","Jawa Timur","Kalimantan Barat","Kalimantan Selatan","Kalimantan Tengah",
      "Kalimantan Timur","Kalimantan Utara","Kepulauan Bangka Belitung","Kepulauan Riau","Lampung","Maluku",
      "Maluku Utara","Nusa Tenggara Barat","Nusa Tenggara Timur","Papua","Papua Barat","Papua Barat Daya",
      "Papua Pegunungan","Papua Selatan","Papua Tengah","Riau","Sulawesi Barat","Sulawesi Selatan",
      "Sulawesi Tengah","Sulawesi Tenggara","Sulawesi Utara","Sumatera Barat","Sumatera Selatan","Sumatera Utara"
    ]
    selected_locations = st.multiselect("Select preferred locations", provinces, default=[], key="test_locs")

    # Subsection: Experience Levels
    st.markdown("#### 🧭 Experience Levels")
    experience_options = [
      "Intern / Entry","Junior (1–3 yrs)","Mid (3–5 yrs)",
      "Senior (5–8 yrs)","Lead / Manager (8+ yrs)"
    ]
    selected_experience = st.multiselect("Select experience levels", experience_options, default=[], key="test_exp")

    if st.button("Save Preferences", type="primary", key="btn_save_prefs"):
      prefs_payload = {
        "job_roles": selected_job_roles,
        "locations": selected_locations,
        "experience_levels": selected_experience
      }
      ok = api.update_preferences_api(logger, prefs_payload)
      st.success("✅ Preferences saved.") if ok else st.error("❌ Saving preferences failed. See logs.")

    # Feedback summary
    if any([new_email, new_password, selected_job_roles, selected_locations, selected_experience]):
      st.success("✅ Input detected across one or more sections (not yet saved).")

  except Exception as e:
    logger.exception(f"❌ Error rendering test report page: {e}")
    st.error("An error occurred while displaying the test report page.")
