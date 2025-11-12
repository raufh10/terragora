import os
import json
import requests
import streamlit as st
from typing import List, Dict, Optional, Tuple
from modules.config import (
  get_backend_api_endpoint,
  get_clamav_api_endpoint,
  get_allowed_mime_types
)

# ===== Auth =====
def create_token(_logger) -> Optional[Dict]:
  try:
    _logger.debug("Calling /query/token to generate ephemeral token")
    resp = requests.post(
      f"{get_backend_api_endpoint()}/token",
      timeout=30
    )
    if resp.status_code == 200:
      try:
        result = resp.json()
      except Exception as e:
        _logger.error(f"Failed to parse token response as JSON: {e}")
        return None
      if result.get("ok") and "token" in result:
        _logger.info("Ephemeral token generated successfully.")
        return result.get("token")
      else:
        _logger.warning(f"Token API returned not-ok: {result}")
        return None
    else:
      _logger.error(f"Token request failed: {resp.status_code} - {resp.text}")
      return None
  except requests.Timeout:
    _logger.error("Token request timed out")
    return None
  except Exception as e:
    _logger.error(f"Exception during token generation: {e}")
    return None

# ===== Admin =====
def send_telegram_notification(message: str) -> bool:
  try:
    payload = {"message": message}
    response = requests.post(
      f"{get_backend_api_endpoint()}/admin/telegram",
      json=payload,
      timeout=15
    )
    return response.status_code == 200
  except Exception as e:
    return False

# ===== Main Page =====
def setup_profile(_logger, profile_dict: Dict) -> Optional[Dict]:
  try:
    if not isinstance(profile_dict, dict) or not profile_dict:
      _logger.error("setup_profile called with invalid profile_dict")
      return None
    _logger.debug("Calling /query/setup_profile")
    resp = requests.post(
      f"{get_backend_api_endpoint()}/query/setup_profile",
      json=profile_dict,
      timeout=60
    )
    if resp.status_code == 200:
      try:
        result = resp.json()
      except Exception as e:
        _logger.error(f"Failed to parse setup_profile response as JSON: {e}")
        return None
      if result.get("ok"):
        _logger.info("✅ Profile saved successfully.")
        return result.get("data")
      _logger.warning(f"⚠️ Save profile returned not-ok: {result}")
      return None
    elif resp.status_code == 400:
      try:
        detail = resp.json().get("detail", "Bad request")
      except Exception as e:
        _logger.error(f"Failed to parse 400 response JSON in setup_profile: {e}")
        detail = "Bad request"
      if detail == "Email is already registered":
        _logger.warning(f"⚠️ Profile setup rejected: {detail}")
        try:
          st.warning(f"⚠️ {detail}")
        except Exception as e:
          _logger.warning(f"Streamlit warning could not be shown: {e}")
      else:
        _logger.warning(f"⚠️ Profile setup rejected: {detail}")
      return None
    else:
      _logger.error(f"❌ Save profile failed: {resp.status_code} - {resp.text}")
      return None
  except requests.Timeout:
    _logger.error("setup_profile request timed out")
    return None
  except Exception as e:
    _logger.error(f"💥 Exception during save_profile: {e}")
    return None

# ===== Analysis Page =====
def get_analysis(_logger, email: str) -> Optional[Dict]:
  try:
    if not email:
      _logger.error("get_analysis called with missing email")
      return None
    payload = {"email": email}
    _logger.debug(f"Calling analysis API with email={email}")
    response = requests.post(
      f"{get_backend_api_endpoint()}/query/analysis",
      data=payload,
      timeout=60
    )
    if response.status_code == 200:
      try:
        result = response.json()
      except Exception as e:
        _logger.error(f"Failed to parse analysis API response as JSON: {e}")
        return None, None
      if result.get("ok"):
        _logger.info("Analysis fetched successfully.")
        return result.get("profile_data"), result.get("matching_data")
      else:
        _logger.warning(f"Analysis API returned not-ok response: {result}")
        return None, None
    else:
      _logger.error(f"Analysis request failed: {response.status_code} - {response.text}")
      return None, None
  except requests.Timeout:
    _logger.error("Analysis request timed out")
    return None, None
  except Exception as e:
    _logger.error(f"Exception during analysis fetch: {e}")
    return None, None

def get_single_analysis(_logger, resume_id: int, matches_id: int) -> Optional[Dict]:
  try:
    if not resume_id or not matches_id:
      _logger.error("get_single_analysis called with missing ids")
      return None
    payload = {"resume_id": resume_id, "matches_id": matches_id}
    _logger.debug(f"Calling analysis API with resume_id={resume_id} & matches_id={matches_id}")
    response = requests.post(
      f"{get_backend_api_endpoint()}/query/single_analysis",
      data=payload,
      timeout=60
    )
    if response.status_code == 200:
      try:
        result = response.json()
      except Exception as e:
        _logger.error(f"Failed to parse analysis API response as JSON: {e}")
        return None
      if result.get("ok"):
        _logger.info("Analysis fetched successfully.")
        return result.get("data")
      else:
        _logger.warning(f"Analysis API returned not-ok response: {result}")
        return None
    else:
      _logger.error(f"Analysis request failed: {response.status_code} - {response.text}")
      return None
  except requests.Timeout:
    _logger.error("Analysis request timed out")
    return None
  except Exception as e:
    _logger.error(f"Exception during analysis fetch: {e}")
    return None

# ===== ClamAV Scan (PDF/DOCX) =====
def scan_resume_bytes(_logger, file_bytes: bytes, filename: str, content_type: str) -> Optional[Dict]:
  try:
    if content_type not in get_allowed_mime_types():
      _logger.warning(f"Disallowed content_type for scan: {content_type}")
      return None
    url = f"{get_clamav_api_endpoint()}/scan"
    _logger.debug(f"Calling ClamAV API at {url} for filename={filename}, content_type={content_type}")
    files = {"file": (filename, file_bytes, content_type)}
    resp = requests.post(url, files=files, timeout=30)
    if resp.status_code == 200:
      try:
        data = resp.json()
      except Exception as e:
        _logger.error(f"Failed to parse ClamAV response as JSON: {e}")
        return None
      infected = bool(data.get("infected", False))
      result = data.get("result", "")
      _logger.info(f"ClamAV scan complete. infected={infected}")
      if infected:
        _logger.warning(f"ClamAV detected infection: {result}")
      return {"infected": infected, "result": result}
    else:
      _logger.error(f"ClamAV scan failed: {resp.status_code} - {resp.text}")
      return None
  except requests.Timeout:
    _logger.error("ClamAV scan request timed out")
    return None
  except Exception as e:
    _logger.error(f"Exception during ClamAV scan: {e}")
    return None

def scan_streamlit_uploaded_file(_logger, uploaded_file) -> Optional[Dict]:
  try:
    if uploaded_file is None:
      _logger.warning("scan_streamlit_uploaded_file called with None")
      return None
    filename = getattr(uploaded_file, "name", "resume")
    content_type = getattr(uploaded_file, "type", "") or ""
    if content_type not in get_allowed_mime_types():
      _logger.warning(f"Disallowed uploaded_file content_type: {content_type}")
      return None
    try:
      file_bytes = uploaded_file.read()
    except Exception as e:
      _logger.error(f"Failed to read uploaded_file bytes: {e}")
      return None
    if not file_bytes:
      _logger.warning("Uploaded file is empty; aborting scan")
      return None
    try:
      uploaded_file.seek(0)
    except Exception as e:
      _logger.warning(f"uploaded_file.seek(0) failed or not supported: {e}")
    return scan_resume_bytes(_logger, file_bytes, filename, content_type)
  except Exception as e:
    _logger.error(f"Exception in scan_streamlit_uploaded_file: {e}")
    return None

# --- Test — API Calls for Test Page ---
def update_email_api(_logger, email: str) -> bool:
  try:
    if not email:
      _logger.error("update_email_api called with empty email")
      return False
    url = f"{get_backend_api_endpoint()}/admin/account/email"
    payload = {"email": email}
    _logger.debug(f"POST {url} payload={payload}")
    resp = requests.post(url, json=payload, timeout=30)
    if resp.status_code == 200:
      _logger.info("✅ Email updated")
      return True
    _logger.error(f"❌ Email update failed: {resp.status_code} - {resp.text}")
    return False
  except requests.Timeout:
    _logger.error("update_email_api timed out")
    return False
  except Exception as e:
    _logger.error(f"update_email_api exception: {e}")
    return False

def update_password_api(_logger, password: str) -> bool:
  try:
    if not password:
      _logger.error("update_password_api called with empty password")
      return False
    url = f"{get_backend_api_endpoint()}/admin/account/password"
    payload = {"password": password}
    _logger.debug(f"POST {url} payload=****")
    resp = requests.post(url, json=payload, timeout=30)
    if resp.status_code == 200:
      _logger.info("✅ Password updated")
      return True
    _logger.error(f"❌ Password update failed: {resp.status_code} - {resp.text}")
    return False
  except requests.Timeout:
    _logger.error("update_password_api timed out")
    return False
  except Exception as e:
    _logger.error(f"update_password_api exception: {e}")
    return False

def delete_account_api(_logger) -> bool:
  try:
    url = f"{get_backend_api_endpoint()}/admin/account/delete"
    _logger.debug(f"POST {url}")
    resp = requests.post(url, json={"confirm": True}, timeout=30)
    if resp.status_code == 200:
      _logger.info("✅ Account deletion requested")
      return True
    _logger.error(f"❌ Delete account failed: {resp.status_code} - {resp.text}")
    return False
  except requests.Timeout:
    _logger.error("delete_account_api timed out")
    return False
  except Exception as e:
    _logger.error(f"delete_account_api exception: {e}")
    return False

def upgrade_subscription_api(_logger, plan_id: int) -> bool:
  try:
    url = f"{get_backend_api_endpoint()}/admin/subscription/upgrade"
    payload = {"plan_id": int(plan_id)}
    _logger.debug(f"POST {url} payload={payload}")
    resp = requests.post(url, json=payload, timeout=30)
    if resp.status_code == 200:
      _logger.info("✅ Subscription upgraded")
      return True
    _logger.error(f"❌ Upgrade failed: {resp.status_code} - {resp.text}")
    return False
  except requests.Timeout:
    _logger.error("upgrade_subscription_api timed out")
    return False
  except Exception as e:
    _logger.error(f"upgrade_subscription_api exception: {e}")
    return False

def cancel_subscription_api(_logger) -> bool:
  try:
    url = f"{get_backend_api_endpoint()}/admin/subscription/cancel"
    _logger.debug(f"POST {url}")
    resp = requests.post(url, json={}, timeout=30)
    if resp.status_code == 200:
      _logger.info("✅ Subscription cancelled")
      return True
    _logger.error(f"❌ Cancel failed: {resp.status_code} - {resp.text}")
    return False
  except requests.Timeout:
    _logger.error("cancel_subscription_api timed out")
    return False
  except Exception as e:
    _logger.error(f"cancel_subscription_api exception: {e}")
    return False

def update_preferences_api(_logger, prefs: Dict) -> bool:
  try:
    if not isinstance(prefs, dict):
      _logger.error("update_preferences_api expects dict")
      return False
    url = f"{get_backend_api_endpoint()}/admin/preferences"
    _logger.debug(f"POST {url} payload keys={list(prefs.keys())}")
    resp = requests.post(url, json=prefs, timeout=30)
    if resp.status_code == 200:
      _logger.info("✅ Preferences updated")
      return True
    _logger.error(f"❌ Preferences update failed: {resp.status_code} - {resp.text}")
    return False
  except requests.Timeout:
    _logger.error("update_preferences_api timed out")
    return False
  except Exception as e:
    _logger.error(f"update_preferences_api exception: {e}")
    return False
