from supabase import Client
from typing import Optional

async def insert(
  supabase: Client,
  logger,
  data: dict
):

  try:
    response = (
      supabase
      .table("submissions")
      .upsert(
        data,
        on_conflict="reddit_id",
      )
      .execute()
    )

    if response.data:
      return True

  except Exception as e:
    logger.error(f"Exception bulk inserting submissions: {e}")
    return False

async def select(
  supabase: Client,
  logger,
  subreddit: str
):

  try:
    response = (
      supabase
      .table("submissions")
      .select("*")
      .eq("subreddit", subreddit)
      .execute()
    )

    if response.data:
      return response.data

  except Exception as e:
    logger.error(f"Exception selecting agenda: {e}")
    return []

async def select_to_label(
  supabase: Client,
  logger,
  subreddit: str
):

  try:
    response = (
      supabase
      .table("submissions")
      .select("*")
      .eq("subreddit", subreddit)
      .is_("category_data", "null")
      .order("data->created_utc", desc="desc")
      .execute()
    )

    if response.data:
      return response.data

  except Exception as e:
    logger.error(f"Exception selecting agenda: {e}")
    return []

async def select_non_test(
  supabase: Client,
  logger,
  subreddit: str
):

  try:
    response = (
      supabase
      .table("submissions")
      .select("*")
      .eq("subreddit", subreddit)
      .is_("test_data", "null")
      .execute()
    )

    if response.data:
      return response.data

  except Exception as e:
    logger.error(f"Exception selecting agenda: {e}")
    return []

async def select_reddit_ids(
  supabase: Client,
  logger,
  subreddit: str
):

  try:
    response = (
      supabase
      .table("submissions")
      .select("reddit_id")
      .eq("subreddit", subreddit)
      .execute()
    )

    if response.data:
      return [item["reddit_id"] for item in response.data]
    else:
      return []

  except Exception as e:
    logger.error(f"Exception selecting agenda: {e}")
    return []

async def update_test_data(
  supabase: Client,
  logger,
  data: list
) -> bool:

  if not data or not isinstance(data, list):
    logger.warning("⚠️ update_category called with empty or invalid data list")
    return False

  success_ids = []
  failed_items = []

  # 1️⃣ First pass — attempt updates
  for item in data:
    submission_id = item.get("submission_id")
    to_insert = item.get("to_insert")

    if not submission_id or not isinstance(to_insert, dict):
      logger.warning(f"⚠️ Skipping invalid item: {item}")
      continue

    try:
      logger.debug(f"📝 Updating submission_id={submission_id} | fields={list(to_insert.keys())}")
      response = (
        supabase
        .table("submissions")
        .update(to_insert)
        .eq("reddit_id", submission_id)
        .execute()
      )

      if response.data:
        success_ids.append(submission_id)
      else:
        failed_items.append(item)

    except Exception as e:
      logger.error(f"💥 Exception updating submission_id={submission_id}: {e}")
      failed_items.append(item)

  # 2️⃣ Check result consistency
  if len(success_ids) == len(data):
    logger.info(f"✅ All {len(success_ids)} submissions updated successfully")
    return True

  logger.warning(f"⚠️ Partial update success: {len(success_ids)}/{len(data)}. Retrying {len(failed_items)} failed.")

  # 3️⃣ Retry failed ones once
  retry_failed = []
  for item in failed_items:
    submission_id = item.get("submission_id")
    to_insert = item.get("to_insert")

    try:
      response = (
        supabase
        .table("submissions")
        .update(to_insert)
        .eq("id", submission_id)
        .execute()
      )
      if response.data:
        success_ids.append(submission_id)
      else:
        retry_failed.append(item)
    except Exception as e:
      logger.error(f"💥 Retry failed for submission_id={submission_id}: {e}")
      retry_failed.append(item)

  if retry_failed:
    logger.error(f"🚫 Still failed after retry: {len(retry_failed)} submissions")
    return False

  logger.info(f"✅ All submissions updated successfully after retry | total={len(success_ids)}")
  return True

async def update_category_data(
  supabase: Client,
  logger,
  data: list
) -> bool:

  if not data or not isinstance(data, list):
    logger.warning("⚠️ update_category called with empty or invalid data list")
    return False

  success_ids = []
  failed_items = []

  # 1️⃣ First pass — attempt updates
  for item in data:
    submission_id = item.get("submission_id")
    to_insert = item.get("to_insert")

    if not submission_id or not isinstance(to_insert, dict):
      logger.warning(f"⚠️ Skipping invalid item: {item}")
      continue

    try:
      logger.debug(f"📝 Updating submission_id={submission_id} | fields={list(to_insert.keys())}")
      response = (
        supabase
        .table("submissions")
        .update(to_insert)
        .eq("id", submission_id)
        .execute()
      )

      if response.data:
        success_ids.append(submission_id)
      else:
        failed_items.append(item)

    except Exception as e:
      logger.error(f"💥 Exception updating submission_id={submission_id}: {e}")
      failed_items.append(item)

  # 2️⃣ Check result consistency
  if len(success_ids) == len(data):
    logger.info(f"✅ All {len(success_ids)} submissions updated successfully")
    return True

  logger.warning(f"⚠️ Partial update success: {len(success_ids)}/{len(data)}. Retrying {len(failed_items)} failed.")

  # 3️⃣ Retry failed ones once
  retry_failed = []
  for item in failed_items:
    submission_id = item.get("submission_id")
    to_insert = item.get("to_insert")

    try:
      response = (
        supabase
        .table("submissions")
        .update(to_insert)
        .eq("id", submission_id)
        .execute()
      )
      if response.data:
        success_ids.append(submission_id)
      else:
        retry_failed.append(item)
    except Exception as e:
      logger.error(f"💥 Retry failed for submission_id={submission_id}: {e}")
      retry_failed.append(item)

  if retry_failed:
    logger.error(f"🚫 Still failed after retry: {len(retry_failed)} submissions")
    return False

  logger.info(f"✅ All submissions updated successfully after retry | total={len(success_ids)}")
  return True
