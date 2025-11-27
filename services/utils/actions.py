import inspect
from typing import List, Optional, Callable, Union
from services.config import settings

def _resolve_action(name: str, logger) -> Optional[Callable]:
  fn = settings.ACTION_REGISTRY.get(name)
  if not fn:
    logger.warning(f"⚠️ No function registered for action '{name}'.")
    return None
  return fn

def _normalize_actions(action_spec: Union[str, List[str]], logger) -> List[str]:
  if isinstance(action_spec, list):
    return [a.strip() for a in action_spec if a and str(a).strip()]
  if isinstance(action_spec, str):
    tmp = action_spec.replace(">", " ").replace(",", " ")
    return [p.strip() for p in tmp.split() if p.strip()]
  logger.warning(f"⚠️ Unsupported action type: {type(action_spec)}; ignoring.")
  return []

def run_actions(action_spec: Union[str, List[str]], logger) -> None:
  names = _normalize_actions(action_spec)
  if not names:
    logger.info("ℹ️ No actions to run.")
    return

  logger.info(f"🧩 Running actions in sequence: {', '.join(names)}")
  for name in names:
    fn = _resolve_action(name)
    if not fn:
      continue
    try:
      sig = inspect.signature(fn)
      if "logger" in sig.parameters:
        logger.info(f"▶️ {name} (with logger)")
        fn(logger=logger)
      else:
        logger.info(f"▶️ {name}")
        fn()
      logger.info(f"✅ {name} completed")
    except Exception as e:
      logger.exception(f"❌ Error while running action '{name}': {e}")
