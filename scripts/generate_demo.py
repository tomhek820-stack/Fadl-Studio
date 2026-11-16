#!/usr/bin/env python3
"""Generate one continuous Arabic narration track and scene-relative word captions."""
from __future__ import annotations
import base64, hashlib, html, json, os, re, shutil, subprocess, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "demo/scenes.json"
GENERATED = ROOT / "demo/generated"
AUDIO_DIR = ROOT / "public/audio"
PIPER_VOICE = "ar_JO-kareem-medium"
PIPER_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/ar/ar_JO/kareem/medium"
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

def duration_frames(path: Path, fps: int = 30) -> int:
    result = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(path)],capture_output=True,text=True,check=True)
    seconds=float(result.stdout.strip())
    if seconds <= 0:
        raise RuntimeError("Generated narration is empty")
    return max(1,round(seconds*fps))

def weights_for(text: str) -> float:
    letters=len(re.findall(r"[\u0600-\u06FF\w]",text))
    punctuation=sum(text.count(mark) for mark in "،؛,.!?؟")
    return max(1,letters)+punctuation*2.5

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

def synthesize_google(scenes: list[dict], target: Path, api_key: str) -> str:
    # One synthesis request preserves phrase-level prosody across scene boundaries.
    parts=[]
    for scene in scenes:
        sentence=html.escape(scene["narration"].strip(),quote=False)
        parts.append(f"<s>{sentence}</s><break time='260ms'/>")
    ssml="<speak><p>"+"".join(parts)+"</p></speak>"
    payload={"input":{"ssml":ssml},
      "voice":{"languageCode":"ar-XA","name":"ar-XA-Chirp3-HD-Charon"},
      "audioConfig":{"audioEncoding":"MP3"}}
    request=urllib.request.Request(
      "https://texttospeech.googleapis.com/v1/text:synthesize?key="+api_key,
      data=json.dumps(payload,ensure_ascii=False).encode("utf-8"),
      headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(request,timeout=120) as response:
        data=json.loads(response.read().decode("utf-8"))
    target_mp3=target.with_suffix(".mp3")
    target_mp3.write_bytes(base64.b64decode(data["audioContent"]))
    subprocess.run(["ffmpeg","-y","-i",str(target_mp3),"-ar","24000","-ac","1","-c:a","pcm_s16le",str(target)],
      check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    target_mp3.unlink(missing_ok=True)
    return "Google Cloud TTS / Chirp 3 HD (ar-XA, Charon)"

def synthesize_piper(scenes: list[dict], target: Path) -> str:
    model_dir=Path(os.environ.get("PIPER_MODEL_DIR",ROOT/".cache/piper"))
    model_dir.mkdir(parents=True,exist_ok=True)
    model=model_dir/(PIPER_VOICE+".onnx")
    config=model_dir/(PIPER_VOICE+".onnx.json")
    download(PIPER_BASE+"/"+PIPER_VOICE+".onnx",model,MODEL_MD5)
    download(PIPER_BASE+"/"+PIPER_VOICE+".onnx.json",config,CONFIG_MD5)
    # Piper receives the complete narration in a single inference, not five isolated clips.
    text=" ".join(s["narration"].strip() for s in scenes)
    subprocess.run(["piper","--model",str(model),"--config",str(config),"--output_file",str(target)],
      input=text+"\n",text=True,check=True)
    normalized=target.with_suffix(".normalized.wav")
    subprocess.run(["ffmpeg","-y","-i",str(target),"-ar","24000","-ac","1","-c:a","pcm_s16le",str(normalized)],
      check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    normalized.replace(target)
    return "Piper / ar_JO-kareem-medium (single continuous synthesis)"

def main() -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("Install FFmpeg and FFprobe first.")
    config=json.loads(SOURCE.read_text(encoding="utf-8"))
    scenes=config["scenes"]
    if len(scenes)!=5:
        raise SystemExit("The social video must contain exactly five scenes.")
    if any(not s.get("narration","").strip() for s in scenes):
        raise SystemExit("Every scene requires narration.")
    AUDIO_DIR.mkdir(parents=True,exist_ok=True)
    target=AUDIO_DIR/"narration.wav"
    api_key=os.environ.get("GOOGLE_TTS_API_KEY","").strip()
    if api_key:
        provider=synthesize_google(scenes,target,api_key)
    else:
        if shutil.which("piper") is None:
            raise SystemExit("Set GOOGLE_TTS_API_KEY or install piper-tts.")
        provider=synthesize_piper(scenes,target)
    total_audio_frames=duration_frames(target)
    if total_audio_frames>900:
        raise SystemExit(f"Narration is {total_audio_frames/30:.1f}s; shorten the script to fit a 30s video.")
    scene_weights=[weights_for(s["narration"]) for s in scenes]
    weight_total=sum(scene_weights)
    frame_allocations=[]; allocated=0
    for i,w in enumerate(scene_weights):
        end=total_audio_frames if i==len(scenes)-1 else max(allocated+1,round(total_audio_frames*sum(scene_weights[:i+1])/weight_total))
        end=min(total_audio_frames,end)
        frame_allocations.append(end-allocated); allocated=end
    output_scenes=[]; cursor=0
    for scene,frames in zip(scenes,frame_allocations):
        words=word_timings(scene["caption"],frames)
        duration=frames
        output_scenes.append({**scene,"audioDurationFrames":frames,"durationInFrames":duration,
          "startFrame":cursor,"wordTimings":words})
        cursor+=duration
    if cursor<900:
        output_scenes[-1]["durationInFrames"]+=900-cursor
        cursor=900
    props={"title":config["title"],"audio":"audio/narration.wav","scenes":output_scenes}
    GENERATED.mkdir(parents=True,exist_ok=True)
    (GENERATED/"props.json").write_text(json.dumps(props,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    metadata={"voice":provider,"speechSpeed":1.0,"audioDurationFrames":total_audio_frames,
      "audioDurationSeconds":round(total_audio_frames/30,3),"totalFrames":cursor,"fps":30,
      "durationSeconds":round(cursor/30,3),"captionMode":"word-by-word estimated scene-relative timing",
      "synthesisMode":"single continuous narration track","scenes":[
        {"id":s["id"],"audioDurationFrames":s["audioDurationFrames"],"wordCount":len(s["wordTimings"])}
        for s in output_scenes]}
    (GENERATED/"metadata.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Generated one continuous narration ({provider}); audio {total_audio_frames/30:.2f}s; video {cursor/30:.2f}s")

if __name__=="__main__":
    main()
