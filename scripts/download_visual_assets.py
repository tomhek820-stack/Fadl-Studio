#!/usr/bin/env python3
"""Download and validate Lucide SVG assets referenced by the video scenes."""
from __future__ import annotations
import json
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "public" / "icons"
PHOTO_DEST = ROOT / "public" / "photos"
PHOTO_SOURCES = ROOT / "demo" / "generated" / "photo-sources.json"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
BASE = "https://cdn.jsdelivr.net/npm/lucide-static@0.468.0/icons/"
BASE_ASSETS = {"shield-check","refresh-cw","sliders-horizontal","lock-keyhole","cloud-upload",
    "sparkles","file-text","audio-lines","captions","upload","shapes","hexagon","orbit",
    "hard-drive","app-window","trash-2","camera","mic","map-pin","settings-2","smartphone","flashlight","contact-round"}

def scene_icons() -> set[str]:
    data=json.loads((ROOT/"demo/scenes.json").read_text(encoding="utf-8"))
    found=set()
    aliases = {"sliders": "sliders-horizontal"}
    for scene in data.get("scenes",[]):
        scene_icon = scene.get("icon","shapes")
        found.add(aliases.get(scene_icon, scene_icon))
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


def image_bytes_ok(data: bytes) -> bool:
    return (data.startswith(b"\\xff\\xd8\\xff") or data.startswith(b"\\x89PNG\\r\\n\\x1a\\n")
            or (data[:4] == b"RIFF" and data[8:12] == b"WEBP"))

def commons_candidates(query: str) -> list[dict]:
    params = {"action":"query","generator":"search","gsrsearch":query,"gsrnamespace":6,
        "gsrlimit":15,"prop":"imageinfo","iiprop":"url|extmetadata","iiurlwidth":1920,
        "format":"json","formatversion":2}
    request=urllib.request.Request(COMMONS_API+"?"+urllib.parse.urlencode(params),
        headers={"User-Agent":"AbuMohammedTechVideo/1.0 (educational video pipeline)"})
    with urllib.request.urlopen(request,timeout=45) as response:
        payload=json.loads(response.read().decode("utf-8"))
    results=[]
    for page in payload.get("query",{}).get("pages",[]):
        info=(page.get("imageinfo") or [{}])[0]
        meta=info.get("extmetadata") or {}
        license_name=re.sub(r"<[^>]+>","",meta.get("LicenseShortName",{}).get("value","")).strip()
        if not re.search(r"CC0|Public domain|CC BY(?:-SA)?(?:\\s|$)",license_name,re.I):
            continue
        url=info.get("thumburl") or info.get("url")
        if not url or not url.startswith("https://upload.wikimedia.org/"):
            continue
        results.append({"title":page.get("title",""),"url":url,"license":license_name,
            "artist":re.sub(r"<[^>]+>","",meta.get("Artist",{}).get("value","")).strip(),
            "credit":re.sub(r"<[^>]+>","",meta.get("Credit",{}).get("value","")).strip()})
    return results

def download_scene_photos() -> None:
    data=json.loads((ROOT/"demo/scenes.json").read_text(encoding="utf-8"))
    scenes=data.get("scenes",[])
    if len(scenes)!=5:
        raise RuntimeError("Photo pipeline expects exactly five scenes")
    PHOTO_DEST.mkdir(parents=True,exist_ok=True)
    sources={}
    for scene in scenes:
        scene_id=scene["id"]
        query=scene.get("visual",{}).get("photoQuery")
        if not isinstance(query,str) or len(query.strip())<8:
            raise RuntimeError(f"Missing meaningful photoQuery for {scene_id}")
        last_error=None
        for candidate in commons_candidates(query):
            try:
                request=urllib.request.Request(candidate["url"],headers={"User-Agent":"AbuMohammedTechVideo/1.0"})
                with urllib.request.urlopen(request,timeout=60) as response:
                    image=response.read()
                if len(image)<20000 or not image_bytes_ok(image):
                    raise ValueError("Invalid or undersized image response")
                target=PHOTO_DEST/(scene_id+".jpg")
                target.write_bytes(image)
                candidate["local"]="photos/"+target.name
                sources[scene_id]=candidate
                scene.setdefault("visual",{})["photo"]=candidate["local"]
                print(f"Photo ready: {scene_id} / {candidate['title']} / {candidate['license']}",flush=True)
                break
            except Exception as exc:
                last_error=exc
                print(f"Skipping invalid Commons candidate for {scene_id}: {exc}",flush=True)
        if scene_id not in sources:
            raise RuntimeError(f"No valid openly licensed photo for {scene_id}; last error: {last_error}")
    PHOTO_SOURCES.parent.mkdir(parents=True,exist_ok=True)
    PHOTO_SOURCES.write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Five unique Wikimedia Commons photos downloaded; attribution metadata saved.")

def main() -> None:
    DEST.mkdir(parents=True,exist_ok=True)
    required=BASE_ASSETS|scene_icons()
    for name in sorted(required):
        fetch(name)
    missing=[name for name in required if not (DEST/f"{name}.svg").is_file()]
    if missing:
        raise RuntimeError("Missing visual assets: "+", ".join(sorted(missing)))
    print(f"Visual assets ready: {len(required)} scene-aware SVG files")
    download_scene_photos()

if __name__=="__main__":
    main()
