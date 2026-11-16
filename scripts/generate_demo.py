#!/usr/bin/env python3
"""Generate demo narration with a locally downloaded Piper Arabic voice."""
from __future__ import annotations
import hashlib, json, os, shutil, subprocess, urllib.request, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "demo/scenes.json"
GENERATED = ROOT / "demo/generated"
AUDIO_DIR = GENERATED / "audio"
VOICE = "ar_JO-kareem-medium"
BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/ar/ar_JO/kareem/medium"
MODEL_MD5 = "c0697df8a7fb180079cc5ac523f91a8e"
CONFIG_MD5 = "dd70b31eb5a395907241b1e5367ace3a"

def download(url: str, destination: Path, expected_md5: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and hashlib.md5(destination.read_bytes()).hexdigest() == expected_md5:
        return
    destination.unlink(missing_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Fadl-Studio/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response, destination.open("wb") as out:
        shutil.copyfileobj(response, out)
    digest = hashlib.md5(destination.read_bytes()).hexdigest()
    if digest != expected_md5:
        destination.unlink(missing_ok=True)
        raise RuntimeError("Checksum mismatch for " + destination.name)

def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wav:
        if wav.getnframes() <= 0 or wav.getframerate() <= 0:
            raise RuntimeError("Invalid/empty WAV: " + str(path))
        if wav.getnchannels() not in (1, 2):
            raise RuntimeError("Unexpected channel count in " + str(path))
        return wav.getnframes() / wav.getframerate()

def main() -> None:
    if shutil.which("piper") is None:
        raise SystemExit("Piper CLI not found. Install with: python3 -m pip install piper-tts")
    config = json.loads(SOURCE.read_text(encoding="utf-8"))
    scenes = config["scenes"]
    if len(scenes) != 5:
        raise SystemExit("The demo must contain exactly five scenes.")
    model_dir = Path(os.environ.get("PIPER_MODEL_DIR", ROOT / ".cache/piper"))
    model_dir.mkdir(parents=True, exist_ok=True)
    model = model_dir / (VOICE + ".onnx")
    model_config = model_dir / (VOICE + ".onnx.json")
    download(BASE + "/" + VOICE + ".onnx", model, MODEL_MD5)
    download(BASE + "/" + VOICE + ".onnx.json", model_config, CONFIG_MD5)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    output_scenes, cursor = [], 0
    for scene in scenes:
        text = scene["narration"].strip()
        if not text:
            raise RuntimeError("Empty narration for " + scene["id"])
        target = AUDIO_DIR / (scene["id"] + ".wav")
        fingerprint = hashlib.sha256((VOICE + "\0" + text).encode("utf-8")).hexdigest()
        stamp = target.with_suffix(".sha256")
        if not target.exists() or not stamp.exists() or stamp.read_text().strip() != fingerprint:
            temp = target.with_suffix(".tmp.wav")
            temp.unlink(missing_ok=True)
            subprocess.run(["piper","--model",str(model),"--config",str(model_config),"--output_file",str(temp)],
                           input=text + "\n", text=True, check=True)
            duration = wav_duration(temp)
            temp.replace(target)
            stamp.write_text(fingerprint + "\n", encoding="utf-8")
        else:
            duration = wav_duration(target)
        duration_frames = max(1, round(duration * 30) + 12)
        output_scenes.append({**scene,"audio":"demo/generated/audio/"+scene["id"]+".wav",
            "audioDurationSeconds":round(duration,3),"durationInFrames":duration_frames,"startFrame":cursor})
        cursor += duration_frames
    props = {"title":config["title"],"scenes":output_scenes}
    GENERATED.mkdir(parents=True,exist_ok=True)
    (GENERATED/"props.json").write_text(json.dumps(props,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    metadata = {"voice":VOICE,"totalFrames":cursor,"fps":30,"durationSeconds":round(cursor/30,3),
      "scenes":[{"id":s["id"],"audioDurationSeconds":s["audioDurationSeconds"],"durationInFrames":s["durationInFrames"]} for s in output_scenes]}
    (GENERATED/"metadata.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Generated five WAV files; timeline: %.2fs" % (cursor/30))

if __name__ == "__main__":
    main()
