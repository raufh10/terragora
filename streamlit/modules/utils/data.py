from modules.document import anonymize_text

def get_resume_text(data: dict, logger):

  if not data:
    return None, None

  if "file" in data:
    resume_text = anonymize_text(data["file"]["data"]["text"], logger)
    return {"data": {"text": resume_text}}, resume_text
  elif "text" in data:
    resume_text = anonymize_text(data["text"]["data"]["text"], logger)
    return {"data": {"text": resume_text}}, resume_text

  return None, None

def refine_responsibility_status(data: list[dict]) -> list[dict]:
  refined = []
  for item in data:
    duty = item.get("duty", "").strip()
    status = item.get("status", "").strip().lower()

    if status == "covered":
      readable = "✅ Met"
    elif status == "not_obvious":
      readable = "❌ Missing / Unknown"
    else:
      readable = "⚪ Unknown"

    refined.append({
      "duty": duty,
      "status": readable
    })
  return refined
