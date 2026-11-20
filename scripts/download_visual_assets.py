#!/usr/bin/env python3
"""Download and validate the Lucide SVG assets used by the Arabic video scenes."""
from __future__ import annotations
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "public" / "icons"
BASE = "https://cdn.jsdelivr.net/npm/lucide-static@0.468.0/icons/"
ASSETS = [
    "shield-check", "refresh-cw", "sliders-horizontal", "lock-keyhole",
    "cloud-upload", "sparkles", "file-text", "audio-lines", "captions",
    "upload", "shapes", "hexagon", "orbit", "hard-drive", "app-window", "trash-2",
]

def fetch(name: str) -> None:
    target = DEST / f"{name}.svg"
    url = BASE + name + ".svg"
    last_error = None
    for attempt in range(1, 5):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Abu-Mohammed-Tech-Video/1.0"})
            with urllib.request.urlopen(request, timeout=35) as response:
                data = response.read()
            text = data.decode("utf-8")
            if len(data) < 100 or "<svg" not in text or "</svg>" not in text:
                raise ValueError("Invalid SVG response")
            target.write_bytes(data)
            print(f"Downloaded {name}.svg ({len(data)} bytes)")
            return
        except Exception as exc:
            last_error = exc
            print(f"Download {name} attempt {attempt}/4 failed: {exc}", flush=True)
            if attempt < 4:
                time.sleep(min(2 ** (attempt - 1), 8))
    raise RuntimeError(f"Could not download required visual asset {name}: {last_error}")

def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for name in ASSETS:
        fetch(name)
    missing = [name for name in ASSETS if not (DEST / f"{name}.svg").is_file()]
    if missing:
        raise RuntimeError("Missing visual assets: " + ", ".join(missing))
    print(f"Visual assets ready: {len(ASSETS)} SVG files")

if __name__ == "__main__":
    main()
