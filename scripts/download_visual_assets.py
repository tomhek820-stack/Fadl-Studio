#!/usr/bin/env python3
"""Download and validate Lucide SVG assets referenced by the video scenes."""
from __future__ import annotations
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "public" / "icons"
BASE = "https://cdn.jsdelivr.net/npm/lucide-static@0.468.0/icons/"
BASE_ASSETS = {"shield-check","refresh-cw","sliders-horizontal","lock-keyhole","cloud-upload",
    "sparkles","file-text","audio-lines","captions","upload","shapes","hexagon","orbit",
    "hard-drive","app-window","trash-2","camera","mic","map-pin","settings-2","smartphone","flashlight","contact-round"}

def scene_icons() -> set[str]:
    data=json.loads((ROOT/"demo/scenes.json").read_text(encoding="utf-8"))
    found=set()
    for scene in data.get("scenes",[]):
        found.add(scene.get("icon","shapes"))
        visual=scene.get("visual",{})
        for item in [visual.get("subject",{}),*visual.get("elements",[])]:
            if item and item.get("icon"):
                found.add(item["icon"])
    return found

def fetch(name: str) -> None:
    if not re.fullmatch(r"[a-z0-9-]+",name):
        raise ValueError(f"Unsafe icon name: {name}")
    target=DEST/f"{name}.svg"
    url=BASE+name+".svg"
    last_error=None
    for attempt in range(1,5):
        try:
            request=urllib.request.Request(url,headers={"User-Agent":"Abu-Mohammed-Tech-Video/1.0"})
            with urllib.request.urlopen(request,timeout=35) as response:
                data=response.read()
            content=data.decode("utf-8")
            if len(data)<100 or "<svg" not in content or "</svg>" not in content:
                raise ValueError("Invalid SVG response")
            target.write_bytes(data)
            print(f"Downloaded {name}.svg ({len(data)} bytes)")
            return
        except Exception as exc:
            last_error=exc
            print(f"Download {name} attempt {attempt}/4 failed: {exc}",flush=True)
            if attempt<4:
                time.sleep(min(2**(attempt-1),8))
    raise RuntimeError(f"Could not download required visual asset {name}: {last_error}")

def main() -> None:
    DEST.mkdir(parents=True,exist_ok=True)
    required=BASE_ASSETS|scene_icons()
    for name in sorted(required):
        fetch(name)
    missing=[name for name in required if not (DEST/f"{name}.svg").is_file()]
    if missing:
        raise RuntimeError("Missing visual assets: "+", ".join(sorted(missing)))
    print(f"Visual assets ready: {len(required)} scene-aware SVG files")

if __name__=="__main__":
    main()
