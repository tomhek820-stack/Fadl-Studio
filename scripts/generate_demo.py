#!/usr/bin/env python3
"""Generate one continuous Arabic narration track: Edge Neural TTS primary, Piper fallback."""
from __future__ import annotations
import asyncio, hashlib, json, os, re, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "demo/scenes.json"
GENERATED = ROOT / "demo/generated"
AUDIO_DIR = ROOT / "public/audio"
EDGE_VOICE = os.getenv("EDGE_TTS_VOICE", "ar-SA-HamedNeural")
EDGE_RETRIES = max(1, int(os.getenv("EDGE_TTS_RETRIES", "3")))
EDGE_TIMEOUT = max(30, int(os.getenv("EDGE_TTS_TIMEOUT_SECONDS", "180")))
PIPER_VOICE = "ar_JO-kareem-medium"
PIPER_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/ar/ar_JO/kareem/medium"
MODEL_MD5 = "c0697df8a7fb180079cc5ac523f91a8e"
CONFIG_MD5 = "dd70b31eb5a395907241b1e5367ace3a"

def run(cmd: list[str], *, input_text: str | None = None) -> None:
    subprocess.run(cmd, input=input_text, text=True, check=True)

def download(url: str, destination: Path, expected_md5: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and hashlib.md5(destination.read_bytes()).hexdigest() == expected_md5:
        return
    destination.unlink(missing_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Fadl-Studio/2.0"})
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as out:
        shutil.copyfileobj(response, out)
    if hashlib.md5(destination.read_bytes()).hexdigest() != expected_md5:
        destination.unlink(missing_ok=True)
        raise RuntimeError("Checksum mismatch for " + destination.name)

def duration_seconds(path: Path) -> float:
    result = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(path)],capture_output=True,text=True,check=True)
    seconds=float(result.stdout.strip())
    if seconds <= 0:
        raise RuntimeError("Generated narration is empty")
    return seconds

def weights_for(text: str) -> float:
    letters=len(re.findall(r"[\u0600-\u06FF\w]",text))
    punctuation=sum(text.count(mark) for mark in "،؛,.!?؟")
    return max(1,letters)+punctuation*3.0

def word_timings(text: str, total_frames: int) -> list[dict]:
    words=re.findall(r"\S+",text.strip())
    if not words:
        raise RuntimeError("Caption has no words")
    weights=[weights_for(word) for word in words]
    total=sum(weights)
    result=[]; cursor=0
    for i,(word,weight) in enumerate(zip(words,weights)):
        end=total_frames if i==len(words)-1 else max(cursor+1,round(total_frames*sum(weights[:i+1])/total))
        end=min(total_frames,end)
        result.append({"text":word,"startFrame":cursor,"endFrame":end})
        cursor=end
    return result

def synthesize_edge(text: str, target: Path) -> tuple[str, int]:
    """Use Edge Neural TTS with bounded retries; fail over only after all attempts."""
    import edge_tts
    mp3=target.with_suffix(".mp3")
    last_error: Exception | None = None
    for attempt in range(1, EDGE_RETRIES + 1):
        mp3.unlink(missing_ok=True)
        target.unlink(missing_ok=True)
        try:
            async def generate():
                communicate=edge_tts.Communicate(text, EDGE_VOICE, rate="+0%", volume="+0%", pitch="+0Hz")
                await asyncio.wait_for(communicate.save(str(mp3)), timeout=EDGE_TIMEOUT)
            asyncio.run(generate())
            if not mp3.is_file() or mp3.stat().st_size < 1024:
                raise RuntimeError("Edge TTS returned an empty or truncated audio file")
            subprocess.run(["ffmpeg","-y","-v","error","-i",str(mp3),"-ar","24000","-ac","1",
                "-c:a","pcm_s16le",str(target)],check=True)
            if not target.is_file() or target.stat().st_size < 2048:
                raise RuntimeError("Edge TTS WAV conversion failed")
            mp3.unlink(missing_ok=True)
            return f"Microsoft Edge Neural TTS / {EDGE_VOICE} (free online)", attempt
        except Exception as exc:
            last_error=exc
            mp3.unlink(missing_ok=True)
            target.unlink(missing_ok=True)
            print(f"Edge TTS attempt {attempt}/{EDGE_RETRIES} failed: {exc}",file=sys.stderr,flush=True)
            if attempt < EDGE_RETRIES:
                time.sleep(min(2 ** (attempt - 1), 8))
    raise RuntimeError(f"Edge TTS failed after {EDGE_RETRIES} attempts: {last_error}") from last_error

def synthesize_piper(text: str, target: Path) -> str:
    """Offline fallback using the existing Arabic Kareem model."""
    model_dir=ROOT/".cache/piper"
    model=model_dir/(PIPER_VOICE+".onnx")
    config=model_dir/(PIPER_VOICE+".onnx.json")
    download(PIPER_BASE+"/"+PIPER_VOICE+".onnx",model,MODEL_MD5)
    download(PIPER_BASE+"/"+PIPER_VOICE+".onnx.json",config,CONFIG_MD5)
    run([sys.executable,"-m","piper","--model",str(model),"--config",str(config),
         "--output_file",str(target)],input_text=text)
    if not target.is_file() or target.stat().st_size < 2048:
        raise RuntimeError("Piper returned an empty audio file")
    return "Piper / ar_JO-kareem-medium (offline fallback)"

def main() -> None:
    data=json.loads(SOURCE.read_text(encoding="utf-8"))
    scenes=data["scenes"]
    if len(scenes) != 5:
        raise RuntimeError("The current social-video composition requires exactly five scenes")
    narration=" ".join(scene["narration"].strip() for scene in scenes)
    if not narration.strip():
        raise RuntimeError("Narration is empty")
    GENERATED.mkdir(parents=True,exist_ok=True)
    AUDIO_DIR.mkdir(parents=True,exist_ok=True)
    audio=AUDIO_DIR/"narration.wav"
    edge_attempts=0
    try:
        voice,edge_attempts=synthesize_edge(narration,audio)
    except Exception as edge_error:
        print(f"Edge TTS unavailable after retries ({edge_error}); switching to Piper fallback.",file=sys.stderr,flush=True)
        voice=synthesize_piper(narration,audio)
    seconds=duration_seconds(audio)
    fps=int(data.get("fps",30))
    total_frames=max(1,round(seconds*fps))
    if seconds > 60:
        raise RuntimeError(f"Narration is {seconds:.1f}s; video limit is 60s. Shorten the script.")
    scene_weights=[max(1,weights_for(s["narration"])) for s in scenes]
    weight_total=sum(scene_weights)
    props_scenes=[]; metadata_scenes=[]; cursor=0
    for i,scene in enumerate(scenes):
        end=total_frames if i==len(scenes)-1 else max(cursor+1,round(total_frames*sum(scene_weights[:i+1])/weight_total))
        end=min(total_frames,end)
        frames=end-cursor
        timings=word_timings(scene["caption"],frames)
        props_scenes.append({**scene,"durationInFrames":frames,"audioDurationFrames":frames,"wordTimings":timings})
        metadata_scenes.append({"id":scene["id"],"audioDurationFrames":frames,"wordCount":len(timings)})
        cursor=end
    props={"title":data["title"],"audio":"audio/narration.wav","scenes":props_scenes}
    (GENERATED/"props.json").write_text(json.dumps(props,ensure_ascii=False,indent=2),encoding="utf-8")
    metadata={"voice":voice,"edgeAttempts":edge_attempts,"audioDurationSeconds":seconds,
        "durationSeconds":seconds,"synthesisMode":"single continuous narration track","scenes":metadata_scenes}
    (GENERATED/"metadata.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Generated {audio} ({seconds:.2f}s) using {voice}; Edge attempts: {edge_attempts}")

if __name__=="__main__":
    main()
