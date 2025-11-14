import os
import json
import requests
import streamlit as st
from typing import List, Dict, Optional, Tuple
from modules.config import get_backend_api_endpoint

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
