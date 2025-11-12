import re
import streamlit as st

class ResumeAnonymizer:
  def __init__(self, text: str, _logger=None):
    self._text = text
    self._logger = _logger

  @classmethod
  def from_text(cls, text: str, _logger=None) -> "ResumeAnonymizer":
    if _logger:
      _logger.info("Initializing ResumeAnonymizer from raw text")
    return cls(text, _logger=_logger)

  @classmethod
  def anonymize(cls, text: str, _logger=None) -> str:
    if _logger:
      _logger.info("🔒 Starting anonymization process")
    try:
      return (
        cls.from_text(text, _logger=_logger)
        .remove_phones()
        .remove_contacts()
        .remove_names()
        .build()
      )
    except Exception as e:
      if _logger:
        _logger.exception(f"❌ Error during anonymization: {e}")
      return text

  def remove_phones(self) -> "ResumeAnonymizer":
    try:
      before_len = len(self._text)
      self._text = re.sub(
        #r"(\+?\d[\d\s().-]{7,}\d)",
        r"(\(?\+?\d[\d\s().-]{7,}\d)",
        "[REDACTED_PHONE]",
        self._text,
      )
      after_len = len(self._text)
      if self._logger:
        self._logger.debug(f"Removed phone numbers | length before={before_len}, after={after_len}")
    except Exception as e:
      if self._logger:
        self._logger.exception(f"Error in remove_phones: {e}")
    return self

  def remove_contacts(self) -> "ResumeAnonymizer":
    try:
      pattern = re.compile(
        r"("
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}|" #Email Addresses
        r"https?://[^\s]+|"
        r"www\.[^\s]+|"
        r"[a-zA-Z0-9.-]+\.[a-z]{2,}(?:/[^\s]*)?|"
        r"@[A-Za-z0-9_]{2,}"
        r")",
        re.IGNORECASE,
      )
      matches = pattern.findall(self._text)
      self._text = pattern.sub("[REDACTED_CONTACT]", self._text)
      if self._logger:
        self._logger.debug(f"Removed {len(matches)} contacts (emails, urls, handles)")
    except Exception as e:
      if self._logger:
        self._logger.exception(f"Error in remove_contacts: {e}")
    return self

  def remove_names(self) -> "ResumeAnonymizer":
    try:
      total_removed = 0
      first_name = None
      last_name = None

      profile = st.session_state.get("user_profile", {})
      name_dict = profile.get("name", {}) or {}

      if name_dict:
        first_name = (name_dict.get("first_name") or "").strip()
        last_name = (name_dict.get("last_name") or "").strip()

      if not ((first_name and len(first_name) >= 2) or (last_name and len(last_name) >= 2)):
        if self._logger:
          self._logger.warning("No session-based first/last name found; skipping name anonymization")
        return self

      f = re.escape(first_name) if first_name else None
      l = re.escape(last_name) if last_name else None

      if f and l:
        self._text, n = re.subn(rf"\b{f}\s+(?:[A-Z]\.\s*)*{l}\b", "[REDACTED_NAME]", self._text, flags=re.IGNORECASE)
        total_removed += n
        self._text, n = re.subn(rf"\b{f}[-\s]+{l}\b", "[REDACTED_NAME]", self._text, flags=re.IGNORECASE)
        total_removed += n
        self._text, n = re.subn(rf"\b{l},?\s+{f}\b", "[REDACTED_NAME]", self._text, flags=re.IGNORECASE)
        total_removed += n
        self._text, n = re.subn(rf"\b{f[0]}(?:\.)?\s+{l}\b", "[REDACTED_NAME]", self._text, flags=re.IGNORECASE)
        total_removed += n
        self._text, n = re.subn(rf"\b{f}\s+{l[0]}(?:\.)?\b", "[REDACTED_NAME]", self._text, flags=re.IGNORECASE)
        total_removed += n
        self._text, n = re.subn(rf"\b{f}\s+(?:\S+\s+){{0,3}}{l}\b", "[REDACTED_NAME]", self._text, flags=re.IGNORECASE)
        total_removed += n
        self._text, n = re.subn(rf"\b{l}\b", "[REDACTED_NAME]", self._text, flags=re.IGNORECASE)
        total_removed += n
        self._text, n = re.subn(rf"\b{f}\b", "[REDACTED_NAME]", self._text, flags=re.IGNORECASE)
        total_removed += n

      elif l:
        self._text, n = re.subn(rf"\b{l}\b", "[REDACTED_NAME]", self._text, flags=re.IGNORECASE)
        total_removed += n

      elif f:
        self._text, n = re.subn(rf"\b{f}\b", "[REDACTED_NAME]", self._text, flags=re.IGNORECASE)
        total_removed += n

      if self._logger:
        self._logger.debug(f"Total name redactions: {total_removed}")

    except Exception as e:
      if self._logger:
        self._logger.exception(f"Error in remove_names: {e}")

    return self

  def build(self) -> str:
    if self._logger:
      self._logger.info("✅ Anonymization complete")
      self._logger.debug(f"Final anonymized text length={len(self._text)}")
    return self._text
