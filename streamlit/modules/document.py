import os
import io
import zipfile
import mimetypes
import streamlit as st
from docx import Document
from modules.utils.anonymize import ResumeAnonymizer

def extract_text_from_pdf(file_bytes: bytes, _logger) -> str:
  import pdfplumber
  try:
    _logger.info("📄 Extracting text from PDF")
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
      text = "\n".join(page.extract_text() or '' for page in pdf.pages)
    _logger.debug(f"Extracted {len(text)} characters from PDF")
    return text
  except Exception as e:
    _logger.exception(f"❌ Error while extracting PDF: {e}")
    return ""

def extract_text_from_docx(
  file_bytes: bytes,
  _logger,
  max_entries: int = 1500,
  max_unzip: int = 80 * 1024 * 1024,
  ratio_limit: int = 15,
  max_paragraphs: int = 5000,
  max_chars: int = 200_000
) -> str:
  try:
    _logger.info("📄 Extracting text from DOCX")
    bio = io.BytesIO(file_bytes)
    with zipfile.ZipFile(bio) as z:
      infos = z.infolist()
      if len(infos) > max_entries:
        raise ValueError("Too many zip entries in DOCX")
      total_unzipped = 0
      for i in infos:
        if i.filename.lower().endswith("vbaproject.bin"):
          raise ValueError("Macros not allowed (.docm)")
        if i.file_size and i.compress_size and (i.file_size / max(1, i.compress_size) > ratio_limit):
          raise ValueError("Abnormal compression ratio in DOCX")
        total_unzipped += i.file_size
        if total_unzipped > max_unzip:
          raise ValueError("DOCX too large when unzipped")

    doc = Document(io.BytesIO(file_bytes))
    parts = []
    for p in doc.paragraphs[:max_paragraphs]:
      if p.text:
        parts.append(p.text)

    text = "\n".join(parts)[:max_chars]
    _logger.debug(f"Extracted {len(text)} characters from DOCX")
    return text
  except Exception as e:
    _logger.exception(f"❌ Error while extracting DOCX: {e}")
    return ""

@st.cache_data
def extract_text(file_ext, file_bytes, _logger) -> str:
  try:
    _logger.info(f"📥 Starting extract_text | mime={file_ext}")
    raw = ""
    if file_ext == 'application/pdf':
      raw = extract_text_from_pdf(file_bytes, _logger)
    elif file_ext == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
      raw = extract_text_from_docx(file_bytes, _logger)
    else:
      _logger.error(f"❌ Unsupported mime type: {file_ext}")
      raise ValueError(f"Unsupported mime type: {file_ext}")

    raw = (raw or "").strip()
    if not raw:
      _logger.warning("⚠️ Extracted text is empty")
      return ""
    _logger.debug(f"Extracted text length={len(raw)}")
    return raw

  except Exception as e:
    _logger.exception(f"❌ Error during extract_text: {e}")
    return ""

def anonymize_text(text: str, _logger) -> str:
  try:
    if not text:
      _logger.warning("⚠️ anonymize_text received empty text; returning empty string")
      return ""
    _logger.info("🔒 Anonymizing extracted text")
    anon_text = ResumeAnonymizer.anonymize(text, _logger)
    _logger.debug(f"Anonymized text length={len(anon_text)}")
    return anon_text
  except Exception as e:
    _logger.exception(f"❌ Error during anonymize_text, returning raw text: {e}")
    return text