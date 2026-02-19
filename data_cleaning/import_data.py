"""
Download ~16GB of the ClickHouse Amazon Reviews Parquet files using a
"stratified by year" approach (spread across time).

"""

from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import requests

BASE_LISTING = "https://datasets-documentation.s3.eu-west-3.amazonaws.com/"
PREFIX = "amazon_reviews/"
OUT_DIR = "data_cleaning/amazon16"
TARGET_GB = 16.0  # stop when downloaded bytes >= TARGET_GB
TARGET_YEARS = [2010, 2011, 2012, 2013, 2014, 2015]

CHUNK_BYTES = 8 * 1024 * 1024
TIMEOUT = 60


@dataclass
class RemoteFile:
    key: str
    url: str
    year: Optional[int]
    size_bytes: Optional[int]


def bytes_to_gb(n: int) -> float:
    return n / (1024**3)


def list_keys(prefix: str) -> List[str]:
    """
    Lists object keys in a public S3 bucket via XML listing.
    Handles pagination via ContinuationToken.
    """
    keys: List[str] = []
    token: Optional[str] = None

    while True:
        params = {"prefix": prefix}
        if token:
            params["continuation-token"] = token

        r = requests.get(BASE_LISTING, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        xml = r.text

        found = re.findall(r"<Key>([^<]+)</Key>", xml)
        keys.extend(found)

        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", xml)
        if not m:
            break
        token = m.group(1)

    # Keep only parquet files
    keys = [k for k in keys if k.endswith(".snappy.parquet")]
    return keys


def infer_year_from_key(key: str) -> Optional[int]:
    # Matches ...amazon_reviews_2015.snappy.parquet
    m = re.search(r"amazon_reviews_(\d{4})\.snappy\.parquet$", key)
    if m:
        return int(m.group(1))
    m = re.search(r"amazon_reviews_(\d{4})s\.snappy\.parquet$", key)
    if m:
        return int(m.group(1))
    return None


def head_size(url: str) -> Optional[int]:
    try:
        r = requests.head(url, allow_redirects=True, timeout=TIMEOUT)
        r.raise_for_status()
        cl = r.headers.get("Content-Length")
        if cl is None:
            return None
        return int(cl)
    except Exception:
        return None


def download_file(url: str, out_path: str) -> int:
    """
    Stream download to disk. Returns bytes written.
    Supports resume if partial file exists (via Range).
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    existing = 0
    if os.path.exists(out_path):
        existing = os.path.getsize(out_path)

    headers = {}
    if existing > 0:
        headers["Range"] = f"bytes={existing}-"

    with requests.get(url, stream=True, headers=headers, timeout=TIMEOUT) as r:
        # If server doesn't support Range, it may return 200; then overwrite
        if r.status_code == 200 and existing > 0:
            existing = 0  # restart
        r.raise_for_status()

        mode = "ab" if existing > 0 else "wb"
        written = existing

        with open(out_path, mode) as f:
            for chunk in r.iter_content(chunk_size=CHUNK_BYTES):
                if not chunk:
                    continue
                f.write(chunk)
                written += len(chunk)

    return written


def main() -> None:
    print("Listing available Parquet files...")
    keys = list_keys(PREFIX)
    if not keys:
        print("No files found. Exiting.")
        sys.exit(1)

    year_to_key: Dict[int, str] = {}
    decade_keys: List[str] = []

    for k in keys:
        y = infer_year_from_key(k)
        if y is None:
            continue
        # Distinguish decades vs exact year
        if k.endswith("s.snappy.parquet"):
            decade_keys.append(k)
        else:
            year_to_key[y] = k

    # (skip missing)
    chosen: List[RemoteFile] = []
    for y in TARGET_YEARS:
        k = year_to_key.get(y)
        if not k:
            print(f"  - Year {y} not available, skipping.")
            continue
        url = BASE_LISTING + k
        chosen.append(RemoteFile(key=k, url=url, year=y, size_bytes=None))

    if not chosen:
        print("None of the target years were found.")
        print("Tip: edit TARGET_YEARS or print available years from the listing.")
        sys.exit(1)

    # Fetch sizes (HEAD) to estimate total before downloading
    print("\nFetching file sizes...")
    for rf in chosen:
        rf.size_bytes = head_size(rf.url)
        if rf.size_bytes is not None:
            print(f"  - {rf.key}: {bytes_to_gb(rf.size_bytes):.2f} GB")
        else:
            print(f"  - {rf.key}: size unknown (no Content-Length)")

    target_bytes = int(TARGET_GB * (1024**3))
    total_planned = sum(rf.size_bytes or 0 for rf in chosen)
    if total_planned > 0:
        print(f"\nPlanned (known sizes only): {bytes_to_gb(total_planned):.2f} GB")
    print(f"Target: {TARGET_GB:.2f} GB\n")

    # Download until target reached
    os.makedirs(OUT_DIR, exist_ok=True)
    downloaded_bytes = 0

    for fname in os.listdir(OUT_DIR):
        if fname.endswith(".parquet"):
            downloaded_bytes += os.path.getsize(os.path.join(OUT_DIR, fname))

    print(f"Already present in {OUT_DIR}/: {bytes_to_gb(downloaded_bytes):.2f} GB\n")

    for rf in chosen:
        if downloaded_bytes >= target_bytes:
            break

        out_name = os.path.basename(rf.key)
        out_path = os.path.join(OUT_DIR, out_name)

        # If file exists and seems complete, skip
        if os.path.exists(out_path) and rf.size_bytes is not None:
            if os.path.getsize(out_path) >= rf.size_bytes:
                print(f"Skipping (already complete): {out_name}")
                continue

        print(f"Downloading: {out_name}")
        start = time.time()
        final_size = download_file(rf.url, out_path)
        elapsed = time.time() - start

        downloaded_bytes = sum(
            os.path.getsize(os.path.join(OUT_DIR, f))
            for f in os.listdir(OUT_DIR)
            if f.endswith(".parquet")
        )

        print(
            f"  Done. File size: {bytes_to_gb(final_size):.2f} GB | "
            f"Folder total: {bytes_to_gb(downloaded_bytes):.2f} GB | "
            f"Time: {elapsed:.1f}s\n"
        )

    print("Finished.")
    print(f"Downloaded total in {OUT_DIR}/: {bytes_to_gb(downloaded_bytes):.2f} GB")
    print("These files are already Parquet. You can read them as a folder of Parquet files.")


if __name__ == "__main__":
    main()
