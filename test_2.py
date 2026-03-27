import requests
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://www.reddit.com"
SUBREDDIT = "jualbeliindonesia"

HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145.0.0.0 Safari/537.36"
}

MAX_WORKERS = 5
CHUNK_SIZE = 10
DELAY_BETWEEN_BATCH = 2


def fetch_posts():
  url = f"{BASE_URL}/r/{SUBREDDIT}.json?limit=100"
  res = requests.get(url, headers=HEADERS, timeout=15)
  data = res.json()

  posts = []

  for child in data["data"]["children"]:
    post = child["data"]

    flair = post.get("link_flair_richtext")
    if not flair:
      continue

    posts.append({
      "id": post.get("id"),
      "permalink": post.get("permalink"),
      "created_utc": post.get("created_utc"),
    })

  return posts


def fetch_size(post):
  try:
    url = f"{BASE_URL}{post['permalink']}.json"

    res = requests.get(url, headers=HEADERS, timeout=10)
    size = len(res.content)

    print(f"{url} -> {size} bytes")

    return size

  except Exception as e:
    print(f"Failed: {post['permalink']} -> {e}")
    return None


def chunk_list(data, size):
  for i in range(0, len(data), size):
    yield data[i:i + size]


def measure_post_sizes(posts):
  sizes = []

  chunks = list(chunk_list(posts, CHUNK_SIZE))

  for idx, chunk in enumerate(chunks):
    print(f"\n--- Processing batch {idx + 1}/{len(chunks)} ---")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
      futures = [executor.submit(fetch_size, post) for post in chunk]

      for future in as_completed(futures):
        result = future.result()
        if result:
          sizes.append(result)

    if idx < len(chunks) - 1:
      print(f"Sleeping {DELAY_BETWEEN_BATCH}s...\n")
      time.sleep(DELAY_BETWEEN_BATCH)

  return sizes


def print_stats(sizes):
  if not sizes:
    print("No data")
    return

  avg = sum(sizes) / len(sizes)
  median = statistics.median(sizes)
  max_size = max(sizes)

  print("\n📊 JSON Stats:")
  print(f"Count: {len(sizes)}")
  print(f"Average: {avg:.2f} bytes ({avg/1024:.2f} KB)")
  print(f"Median: {median:.2f} bytes ({median/1024:.2f} KB)")
  print(f"Max: {max_size} bytes ({max_size/1024:.2f} KB)")


if __name__ == "__main__":
  posts = fetch_posts()
  print(f"Filtered posts: {len(posts)}")

  sizes = measure_post_sizes(posts)
  print_stats(sizes)
