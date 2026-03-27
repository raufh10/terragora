import requests
import statistics
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://www.reddit.com"
SUBREDDIT = "jualbeliindonesia"

HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145.0.0.0 Safari/537.36"
}

MAX_WORKERS = 5
CHUNK_SIZE = 10
DELAY_BETWEEN_BATCH = 2
MAX_RETRIES = 3


def normalize_flair(flair_text):
  if not flair_text:
    return "UNKNOWN"

  flair_text = flair_text.upper()

  if ":" in flair_text:
    return flair_text.split(":")[0].strip()

  return flair_text.strip()


def safe_get_json(url):
  for attempt in range(MAX_RETRIES):
    try:
      res = requests.get(url, headers=HEADERS, timeout=15)

      # Debug status
      if res.status_code != 200:
        print(f"⚠️ Status {res.status_code} for {url}")
        time.sleep(2)
        continue

      # Check if response looks like JSON
      if not res.text.strip().startswith("{") and not res.text.strip().startswith("["):
        print(f"⚠️ Non-JSON response for {url}")
        time.sleep(2)
        continue

      return res.json()

    except Exception as e:
      print(f"Retry {attempt+1} failed: {e}")
      time.sleep(2)

  print(f"❌ Failed to fetch JSON: {url}")
  return None


def fetch_posts():
  url = f"{BASE_URL}/r/{SUBREDDIT}.json?limit=100"
  data = safe_get_json(url)

  if not data:
    return []

  posts = []

  for child in data["data"]["children"]:
    post = child["data"]

    flair = post.get("link_flair_richtext")
    if not flair:
      continue

    raw_flair = flair[0].get("t", "UNKNOWN")
    normalized_flair = normalize_flair(raw_flair)

    posts.append({
      "permalink": post.get("permalink"),
      "flair": normalized_flair,
    })

  return posts


def fetch_size(post):
  url = f"{BASE_URL}{post['permalink']}.json"

  for attempt in range(MAX_RETRIES):
    try:
      res = requests.get(url, headers=HEADERS, timeout=10)

      if res.status_code != 200:
        print(f"⚠️ {res.status_code} for {url}")
        time.sleep(1)
        continue

      size = len(res.content)

      print(f"{post['flair']} -> {size} bytes")

      return (post["flair"], size)

    except Exception as e:
      print(f"Retry {attempt+1} failed: {e}")
      time.sleep(1)

  print(f"❌ Failed: {url}")
  return None


def chunk_list(data, size):
  for i in range(0, len(data), size):
    yield data[i:i + size]


def measure_sizes(posts):
  all_sizes = []
  flair_sizes = defaultdict(list)

  chunks = list(chunk_list(posts, CHUNK_SIZE))

  for idx, chunk in enumerate(chunks):
    print(f"\n--- Batch {idx + 1}/{len(chunks)} ---")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
      futures = [executor.submit(fetch_size, post) for post in chunk]

      for future in as_completed(futures):
        result = future.result()
        if result:
          flair, size = result
          all_sizes.append(size)
          flair_sizes[flair].append(size)

    if idx < len(chunks) - 1:
      print(f"Sleeping {DELAY_BETWEEN_BATCH}s...\n")
      time.sleep(DELAY_BETWEEN_BATCH)

  return all_sizes, flair_sizes


def print_stats(all_sizes, flair_sizes):
  if not all_sizes:
    print("No data collected")
    return

  avg = sum(all_sizes) / len(all_sizes)
  median = statistics.median(all_sizes)

  print("\n📊 Overall Stats:")
  print(f"Count: {len(all_sizes)}")
  print(f"Average: {avg:.2f} bytes ({avg/1024:.2f} KB)")
  print(f"Median: {median:.2f} bytes ({median/1024:.2f} KB)")
  print(f"Max: {max(all_sizes)} bytes ({max(all_sizes)/1024:.2f} KB)")

  print("\n📊 Normalized Flair Stats:\n")

  for flair, sizes in sorted(flair_sizes.items(), key=lambda x: len(x[1]), reverse=True):
    count = len(sizes)
    avg = sum(sizes) / count
    median = statistics.median(sizes)

    print(f"{flair}:")
    print(f"  Count: {count}")
    print(f"  Avg: {avg:.2f} bytes ({avg/1024:.2f} KB)")
    print(f"  Median: {median:.2f} bytes ({median/1024:.2f} KB)")
    print(f"  Max: {max(sizes)} bytes ({max(sizes)/1024:.2f} KB)")
    print()


if __name__ == "__main__":
  posts = fetch_posts()
  print(f"Filtered posts: {len(posts)}")

  if not posts:
    print("❌ No posts fetched. Likely rate-limited.")
  else:
    all_sizes, flair_sizes = measure_sizes(posts)
    print_stats(all_sizes, flair_sizes)
