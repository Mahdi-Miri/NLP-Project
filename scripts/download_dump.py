import argparse
import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests
from tqdm import tqdm
from config.settings import config

DEFAULT_DUMP_URL = "https://dumps.wikimedia.org/enwikiquote/latest/enwikiquote-latest-pages-articles.xml.bz2"


def download_dump(url: str = DEFAULT_DUMP_URL, destination: Path = None, max_bytes: int = None) -> Path:
    """
    Downloads Wikimedia dump with real-time progress bar.
    Optionally stops after max_bytes if downloading a lightweight test slice.
    """
    if destination is None:
        filename = url.split("/")[-1]
        destination = config.paths.raw_data_dir / filename

    destination.parent.mkdir(parents=True, exist_ok=True)

    print(f"[*] Connecting to: {url}")
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))
    if max_bytes and total_size:
        total_size = min(total_size, max_bytes)

    print(f"[*] Downloading to: {destination} (Total size: {total_size / (1024*1024):.2f} MB)")

    bytes_written = 0
    chunk_size = 1024 * 64

    with open(destination, "wb") as f, tqdm(
        total=total_size, unit="B", unit_scale=True, desc=destination.name
    ) as pbar:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))
                bytes_written += len(chunk)
                if max_bytes and bytes_written >= max_bytes:
                    print(f"\n[*] Reached requested limit of {max_bytes / (1024*1024):.2f} MB.")
                    break

    print(f"[+] Download complete: {destination}")
    return destination


def main():
    parser = argparse.ArgumentParser(description="Download Wikiquote dump file.")
    parser.add_argument("--url", default=DEFAULT_DUMP_URL, help="URL of Wikiquote dump")
    parser.add_argument("--limit-mb", type=float, default=None, help="Stop after downloading N megabytes (for quick testing)")
    args = parser.parse_args()

    max_b = int(args.limit_mb * 1024 * 1024) if args.limit_mb else None
    download_dump(url=args.url, max_bytes=max_b)


if __name__ == "__main__":
    main()
