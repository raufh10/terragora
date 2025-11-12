import os
import re

def get_backend_api_endpoint():
  endpoint = os.getenv("BACKEND_API_ENDPOINT")

  if not endpoint:
    raise EnvironmentError("Missing required environment variable: API_ENDPOINT")
  return endpoint

def get_clamav_api_endpoint():
  endpoint = os.getenv("CLAMAV_API_ENDPOINT")

  if not endpoint:
    raise EnvironmentError("Missing required environment variable: CLAMAV_API_ENDPOINT")
  return endpoint

def get_allowed_mime_types():
  return (
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  )

def get_email_regex():
  return re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

def get_preferences():
  return {
    "job_roles": ["data_analyst"],
    "locations": ["all"],
    "experience_levels": ["entry_level"]
  }
