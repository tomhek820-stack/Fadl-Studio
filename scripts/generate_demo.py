#!/usr/bin/env python3
"""Generate accelerated Arabic narration and word-level caption timing."""
from __future__ import annotations
import hashlib, json, os, re, shutil, subprocess, urllib.request, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "demo/scenes.json"
GENERATED = ROOT / "demo/generated"
AUDIO_DIR = ROOT / "public/audio"
VOICE = "ar_JO-kareem-medium"
SPEECH_SPEED = 1.08
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
    if hashlib.md5(destination.read_bytes()).hexdigest() != expected_md5:
        destination.unlink(missing_ok=True)
        raise RuntimeError("Checksum mismatch for " + destination.name)

def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wav:
        if wav.getnframes() <= 0 or wav.getframerate() <= 0:
            raise RuntimeError("Invalid/empty WAV: " + str(path))
        return wav.getnframes() / wav.getframerate()

def word_timings(text: str, total_frames: int) -> list[dict]:
    words = re.findall(r"\S+", text.strip())
    if not words:
        raise RuntimeError("Caption has no words")
    # Character-weighted estimates, with extra dwell for punctuation.
    weights = []
    for word in words:
        letters = len(re.findall(r"[\u0600-\u06FF\w]", word))
        punctuation = sum(word.count(mark) for mark in "،؛,.!?؟")
        weights.append(max(1, letters) + punctuation * 2.0)
    total = sum(weights)
    result, cursor = [], 0
    for index, (word, weight) in enumerate(zip(words, weights)):
        end = total_frames if index == len(words)-1 else max(cursor+1, round(total_frames * sum(weights[:index+1]) / total))
        end = min(total_frames, end)
        result.append({"text":word,"startFrame":cursor,"endFrame":end})
        cursor = end
    return result

def main() -> None:
    if shutil.which("piper") is None or shutil.which("ffmpeg") is None:
        raise SystemExit("Install piper-tts==1.3.0 and FFmpeg first.")
    config = json.loads(SOURCE.read_text(encoding="utf-8"))
    scenes = config["scenes"]
    if len(scenes) != 5:
        raise SystemExit("The social video must contain exactly five scenes.")
    speed = float(config.get("speechSpeed", SPEECH_SPEED))
    if not 1.0 <= speed <= 1.15:
        raise SystemExit("speechSpeed must be between 1.00 and 1.15.")
    model_dir = Path(os.environ.get("PIPER_MODEL_DIR", ROOT / ".cache/piper"))
    model_dir.mkdir(parents=True, exist_ok=True)
    model = model_dir / (VOICE + ".onnx")
    model_config = model_dir / (VOICE + ".onnx.json")
    download(BASE + "/" + VOICE + ".onnx", model, MODEL_MD5)
    download(BASE + "/" + VOICE + ".onnx.json", model_config, CONFIG_MD5)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    output_scenes, cursor = [], 0
    for scene in scenes:
        narration = scene["narration"].strip()
        if not narration:
            raise RuntimeError("Empty narration for " + scene["id"])
        target = AUDIO_DIR / (scene["id"] + ".wav")
        raw = AUDIO_DIR / (scene["id"] + ".raw.wav")
        fingerprint = hashlib.sha256((VOICE + "\0" + str(speed) + "\0" + narration).encode("utf-8")).hexdigest()
        stamp = target.with_suffix(".sha256")
        if not target.exists() or not stamp.exists() or stamp.read_text().strip() != fingerprint:
            raw.unlink(missing_ok=True)
            subprocess.run(["piper","--model",str(model),"--config",str(model_config),"--output_file",str(raw)],
                           input=narration + "\n", text=True, check=True)
            subprocess.run(["ffmpeg","-y","-i",str(raw),"-filter:a",f"atempo={speed:.2f}",
                            "-acodec","pcm_s16le","-ar","22050","-ac","1",str(target)],
                           check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            raw.unlink(missing_ok=True)
            stamp.write_text(fingerprint + "\n", encoding="utf-8")
        duration = wav_duration(target)
        audio_frames = max(1, round(duration * 30))
        words = word_timings(scene["caption"], audio_frames)
        duration_frames = audio_frames + 12
        output_scenes.append({**scene,"audio":"audio/"+scene["id"]+".wav",
            "audioDurationSeconds":round(duration,3),"audioDurationFrames":audio_frames,
            "durationInFrames":duration_frames,"startFrame":cursor,"wordTimings":words})
        cursor += duration_frames
    # Keep the spoken content intact; only extend the final visual hold to 30s.
    if cursor < 900:
        output_scenes[-1]["durationInFrames"] += 900 - cursor
        cursor = 900
    props = {"title":config["title"],"scenes":output_scenes}
    GENERATED.mkdir(parents=True,exist_ok=True)
    (GENERATED/"props.json").write_text(json.dumps(props,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    metadata = {"voice":VOICE,"speechSpeed":speed,"totalFrames":cursor,"fps":30,
      "durationSeconds":round(cursor/30,3),"captionMode":"word-by-word estimated timing",
      "scenes":[{"id":s["id"],"audioDurationSeconds":s["audioDurationSeconds"],
      "audioDurationFrames":s["audioDurationFrames"],"durationInFrames":s["durationInFrames"],
      "wordCount":len(s["wordTimings"])} for s in output_scenes]}
    (GENERATED/"metadata.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Generated five accelerated WAV files at {speed:.0%} playback rate; timeline: {cursor/30:.2f}s")

if __name__ == "__main__":
    main()
