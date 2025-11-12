import streamlit as st
import pandas as pd
from typing import Dict, Any
from modules.mock import build_mock_analysis
from modules.utils.data import refine_responsibility_status

def render_expanders_only(item, logger):
  try:
    logger.info("Rendering full report inside single expander")

    with st.expander("📄 Full Report Summary"):

      # --- Skills ---
      qf = (item.get("quick_fit") or {})
      strengths = (qf.get("strengths") or [])
      gaps = (qf.get("missing_areas") or [])

      c1, c2 = st.columns(2)
      with c1:
        st.write("**💪 Strengths**")
        if strengths:
          for s in strengths:
            if isinstance(s, str) and s.strip():
              st.write(f"✅ {s}")
        else:
          st.info("No strong matches identified.")
      with c2:
        st.write("**⚠️ Skill Gaps**")
        if gaps:
          for g in gaps:
            if isinstance(g, str) and g.strip():
              st.write(f"❌ {g}")
        else:
          st.success("No major gaps detected! 🎉")

      # --- Requirements ---
      st.write("###### 📋 Requirements")
      er = (item.get("essential_requirements") or {})
      deg_req = er.get("degree_required")
      deg_met = er.get("degree_met")
      req_yrs = er.get("experience_required_years")
      est_yrs = er.get("experience_estimated_years")
      exp_met = er.get("experience_met")

      c1, c2 = st.columns(2)
      with c1:
        st.write("**🎓 Degree**")
        st.write(f"**Requirement:** {'Yes' if deg_req is True else 'No' if deg_req is False else 'Not specified'}")
        st.write(f"**Candidate:** {'✅ Meets requirement' if deg_met is True else '❌ Does not meet' if deg_met is False else '🤔 Not determined'}")
      with c2:
        st.write("**💼 Experience**")
        st.write(f"**Requirement:** {req_yrs if req_yrs is not None else 'Not specified'} years")
        st.write(f"**Candidate Estimate:** {est_yrs if est_yrs is not None else 'Not determined'} years")
        st.write(f"**Match:** {'✅ Meets requirement' if exp_met is True else '❌ Below requirement' if exp_met is False else '🤔 Not determined'}")

      # --- Coverage ---
      rc = (item.get("responsibilities_lite") or {})
      items = refine_responsibility_status(rc.get("items_top5") or [])
      ratio = rc.get("coverage_ratio")

      try:
        value = f"{float(ratio) * 100:.0f}%" if isinstance(ratio, (int, float, str)) else "0%"
      except Exception:
        value = "0%"
      st.metric("###### 🧭 Coverage Ratio", value)

      if items:
        try:
          df = pd.DataFrame(items)[["duty", "status"]]
          df.columns = ["📌 Responsibility", "Status"]
          st.dataframe(df, width="stretch", hide_index=True)
        except Exception as e:
          logger.warning(f"Failed to render coverage table, showing raw: {e}")
          st.write(items)
      else:
        st.info("No key responsibilities mapped.")

      # --- Keywords Suggestions ---
      st.write("###### 🔑 Keywords Suggestions")
      kh = (item.get("keyword_hints") or {})
      add_terms = (kh.get("add_these_terms_top5") or [])

      if add_terms:
        try:
          chips = " ".join(f"`{t}`" for t in add_terms if isinstance(t, str) and t.strip())
          st.markdown(chips or "_No valid keywords to display._")
        except Exception as e:
          logger.warning(f"Failed to render keywords; showing raw: {e}")
          st.write(add_terms)
      else:
        st.success("Looks good — no critical keywords missing!")

  except Exception as e:
    logger.error(f"Error in render_expanders_only: {e}")

class ReportPageBuilder:
  def __init__(self, logger, analysis: Dict[str, Any]):
    self.logger = logger
    try:
      if not analysis:
        self.logger.info("No analysis provided; building mock analysis")
        analysis = build_mock_analysis()
      self.analysis = analysis
      self._built = False
      self.logger.debug(f"ReportPageBuilder initialized | keys={list(self.analysis.keys()) if isinstance(self.analysis, dict) else 'N/A'}")
    except Exception as e:
      self.logger.error(f"Error in __init__: {e}")
      self.analysis = {}
      self._built = False

  def header(self):
    try:
      self.logger.info("Rendering header")

      job_title = self.analysis.get("tailor_tip", {}).get("target_role_title", "")
      if job_title:
        st.markdown(f"<h3 style='text-align:center;'>📊 {job_title} Compatibility Report</h3>", unsafe_allow_html=True)
      else:
        st.markdown("<h3 style='text-align:center;'>📊 Job Compability Report</h3>", unsafe_allow_html=True)

      st.divider()
    except Exception as e:
      self.logger.error(f"Error in header: {e}")
    return self

  def quick_fit_summary(self):
    try:
      self.logger.info("Rendering quick_fit_summary")
      qf = self.analysis.get("quick_fit", {}) or {}
      st.markdown("### 🧾 Compability Score")
      score = qf.get("likely_match_percent", 0)
      self.logger.debug(f"Quick fit score: {score}")

      try:
        st.metric("**💯 Overall Match**", f"{float(score):.0f}%" if isinstance(score, (int, float, str)) else "0%")
      except Exception as e:
        self.logger.warning(f"Failed to render overall match metric, defaulting to 0%: {e}")
        st.metric("**💯 Overall Match**", "0%")

      try:
        message_width = 400
        s_val = float(score) if isinstance(score, (int, float, str)) else 0.0
        if s_val >= 80:
          st.success("Great alignment!", icon="🎉")
        elif s_val >= 60:
          st.warning("Decent fit, a few gaps to close.", icon="⚠️")
        else:
          st.error("Low match, needs tailoring.", icon="🚨")
      except Exception as e:
        self.logger.warning(f"Could not interpret score; showing neutral message: {e}")
        st.info("Match score unavailable.")

      st.markdown("### 🧰 Key Strengths & Skill Gaps")
      skills_c1, skills_c2 = st.columns(2)
      with skills_c1:
        st.write("**💪 Strengths**")
        strengths = qf.get("strengths", []) or []
        if strengths:
          for s in strengths:
            st.write(f"✅ {s}")
        else:
          st.info("No strong matches identified.")
      with skills_c2:
        st.write("**⚠️ Skill Gaps**")
        missing = qf.get("missing_areas", []) or []
        if missing:
          for m in missing:
            st.write(f"❌ {m}")
        else:
          st.success("No major gaps detected! 🎉")
      st.write("")
    except Exception as e:
      self.logger.error(f"Error in quick_fit_summary: {e}")
    return self

  def essentials_section(self):
    try:
      self.logger.info("Rendering essentials_section")
      st.markdown("### 📋 Essential Criteria Overview")
      er = self.analysis.get("essential_requirements", {}) or {}
      self.logger.debug(f"Essentials keys: {list(er.keys()) if isinstance(er, dict) else 'N/A'}")

      col1, col2 = st.columns(2)
      with col1:
        st.write("**🎓 Degree**")
        deg_req = er.get("degree_required")
        deg_met = er.get("degree_met")
        st.write(f"**Requirement:** {'Yes' if deg_req is True else 'No' if deg_req is False else 'Not specified'}")
        st.write(f"**Candidate:** {'✅ Meets requirement' if deg_met is True else '❌ Does not meet' if deg_met is False else '🤔 Not determined'}")

      with col2:
        st.write("**💼 Experience**")
        req_yrs = er.get("experience_required_years")
        est_yrs = er.get("experience_estimated_years")
        exp_met = er.get("experience_met")
        st.write(f"**Requirement:** {req_yrs if req_yrs is not None else 'Not specified'} years")
        st.write(f"**Candidate Estimate:** {est_yrs if est_yrs is not None else 'Not determined'} years")
        st.write(f"**Match:** {'✅ Meets requirement' if exp_met is True else '❌ Below requirement' if exp_met is False else '🤔 Not determined'}")
    except Exception as e:
      self.logger.error(f"Error in essentials_section: {e}")
    return self

  def responsibilities_section(self):
    try:
      self.logger.info("Rendering responsibilities_section")
      st.markdown("### 🧭 Role Responsibilities Overview")
      rc = self.analysis.get("responsibilities_lite", {}) or {}
      items = refine_responsibility_status(rc.get("items_top5", []) or [])
      self.logger.debug(f"Responsibilities items count: {len(items)}")
      ratio = rc.get("coverage_ratio", None)

      if items:
        try:
          try:
            if isinstance(ratio, (int, float, str)):
              value = f"{float(ratio) * 100:.0f}%"
            else:
              value = "0%"
            st.metric("**📊 Coverage Ratio**", value)
          except Exception as e:
            self.logger.warning(f"Failed to compute coverage ratio metric, defaulting to 0%: {e}")
            st.metric("**📊 Coverage Ratio**", "0%")

          df = pd.DataFrame(items)[["duty", "status"]]
          df.columns = ["📌 Responsibility", "Status"]
          st.markdown("**Top Job Duties & Coverage**")
          st.dataframe(df, width="stretch", hide_index=True)
        except Exception as e:
          self.logger.warning(f"Failed to build responsibilities dataframe; showing raw items: {e}")
          st.write(items)
      else:
        st.warning("⚠️ No key responsibilities could be mapped from the job description.")

    except Exception as e:
      self.logger.error(f"Error in responsibilities_section: {e}")
    return self

  def callouts(self):
    try:
      self.logger.info("Rendering callouts")
      kh = self.analysis.get("keyword_hints", {}) or {}
      tt = self.analysis.get("tailor_tip", {}) or {}
      add_terms = kh.get("add_these_terms_top5", []) or []
      suggestion = tt.get("suggestion")
      target_role = tt.get("target_role_title")
      mapped_task = tt.get("mapped_jd_task")
      self.logger.debug(f"Callouts | add_terms={len(add_terms)} suggestion_present={bool(suggestion)}")

      st.divider()
      st.markdown("**🔑 Add These Keywords to Strengthen Your Fit**")
      if add_terms:
        try:
          chips = " ".join(f"`{t}`" for t in add_terms if isinstance(t, str) and t.strip())
          st.markdown(chips or "_No valid keywords to display._")
        except Exception as e:
          if getattr(self, "logger", None):
            self.logger.warning(f"Failed to render add_terms; writing raw list: {e}")
          st.write(add_terms)
      else:
        st.success("🎉 Great news — no critical keywords missing!")

      st.markdown("**✍️ Add This Bullet to Highlight Your Impact**")
      if suggestion:
        st.markdown(f"> {suggestion}")
      else:
        st.info("🤔 No tailored bullet suggestion right now — your resume already covers the essentials.")

    except Exception as e:
      self.logger.error(f"Error in callouts: {e}")
    return self

  def render(self):
    try:
      self._built = True
      self.logger.info("Report render flag set to True")
    except Exception as e:
      self.logger.error(f"Error in render: {e}")
    return self

  def render_full(self):
    try:
      self.logger.info("Rendering full report")
      return (
        self
          .header()
          .quick_fit_summary()
          .essentials_section()
          .responsibilities_section()
          .callouts()
          .render()
      )
    except Exception as e:
      self.logger.error(f"Error in render_full: {e}")
      return self

  @classmethod
  def show(cls, logger, response):
    try:
      logger.info("ReportPageBuilder.show invoked")
      builder = cls(logger=logger, analysis=response)
      builder.render_full()
    except Exception as e:
      logger.error(f"Error in ReportPageBuilder.show: {e}")
      st.error("An error occurred while rendering the report.")
