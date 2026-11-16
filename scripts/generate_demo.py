#!/usr/bin/env python3
"""Generate one continuous Arabic narration track and scene-relative word captions."""
from __future__ import annotations
import hashlib, json, os, re, shutil, subprocess
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

def synthesize_google(scenes: list[dict], target: Path) -> str:
    # Gemini TTS handles the complete script in one generation for continuous prosody.
    from google.cloud import texttospeech
    full_text=" ".join(scene["narration"].strip() for scene in scenes)
    prompt=("اقرأ النص باللغة العربية الفصحى الحديثة بصوت رجل عربي طبيعي ودافئ. "
      "اجعل الأداء كتعليق وثائقي تقني احترافي: نبرة واثقة وودودة، إيقاع محادثة طبيعي، "
      "تنويع لطيف في طبقة الصوت والتأكيد على الكلمات المهمة، وصل الكلمات بسلاسة، "
      "وقفات قصيرة طبيعية عند علامات الترقيم. لا تتحدث بسرعة، ولا تقرأ كروبوت أو كمذيع آلي.")
    client=texttospeech.TextToSpeechClient()
    synthesis_input=texttospeech.SynthesisInput(text=full_text,prompt=prompt)
    voice=texttospeech.VoiceSelectionParams(
      language_code="ar-001",name="Charon",model_name="gemini-3.1-flash-tts-preview")
    audio_config=texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response=client.synthesize_speech(input=synthesis_input,voice=voice,audio_config=audio_config)
    temp=target.with_suffix(".mp3")
    temp.write_bytes(response.audio_content)
    subprocess.run(["ffmpeg","-y","-i",str(temp),"-ar","24000","-ac","1","-c:a","pcm_s16le",str(target)],
      check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    temp.unlink(missing_ok=True)
    return "Google Gemini 3.1 Flash TTS Preview / Charon (Arabic World ar-001)"

