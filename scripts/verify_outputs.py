#!/usr/bin/env python3
"""Strict delivery gate for the two final MP4 exports."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "demo" / "output"
REPORT = ROOT / "demo" / "quality-report.md"
EXPECTED = {
    "final_9x16.mp4": (1080, 1920),
    "final_16x9.mp4": (1920, 1080),
}

def fail(message: str) -> None:
    raise SystemExit("DELIVERY CHECK FAILED: " + message)

def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size:stream=codec_type,codec_name,width,height",
         "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)

def main() -> None:
    if not REPORT.is_file() or REPORT.stat().st_size < 300:
        fail("quality report is missing or unexpectedly small")
    for filename, dimensions in EXPECTED.items():
        path = OUTPUT / filename
        if not path.is_file():
            fail(f"missing export: {path}")
        if path.stat().st_size < 100_000:
            fail(f"export is too small to be a valid finished video: {filename}")
        data = probe(path)
        streams = data.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
        if not video or not audio:
            fail(f"{filename} must contain both video and audio streams")
        if video.get("codec_name") != "h264":
            fail(f"{filename} video codec must be H.264")
        if audio.get("codec_name") != "aac":
            fail(f"{filename} audio codec must be AAC")
        actual = (video.get("width"), video.get("height"))
        if actual != dimensions:
            fail(f"{filename} dimensions {actual} do not match {dimensions}")
        duration = float(data.get("format", {}).get("duration", 0))
        if not 5 <= duration <= 180:
            fail(f"{filename} has implausible duration: {duration}")
        print(f"PASS {filename}: {actual[0]}x{actual[1]}, {duration:.2f}s, H.264 + AAC, {path.stat().st_size} bytes")
    print("DELIVERY CHECK PASSED: both aspect ratios and the quality report are ready.")

if __name__ == "__main__":
    main()
