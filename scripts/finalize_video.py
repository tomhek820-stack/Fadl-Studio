#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

def run(args):
    return subprocess.run(args,check=True,text=True,capture_output=True).stdout

def main():
    if len(sys.argv)!=3:
        raise SystemExit("Usage: finalize_video.py INPUT.mp4 OUTPUT.mp4")
    source,output=map(Path,sys.argv[1:])
    output.parent.mkdir(parents=True,exist_ok=True)
    if not source.exists():
        raise SystemExit("Missing Remotion render: "+str(source))
    subprocess.run(["ffmpeg","-y","-i",str(source),"-map","0:v:0","-map","0:a:0",
      "-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",
      "-c:a","aac","-b:a","192k","-af","loudnorm=I=-16:TP=-1.5:LRA=11",
      "-movflags","+faststart","-shortest",str(output)],check=True)
    probe=json.loads(run(["ffprobe","-v","error","-show_entries",
      "format=duration:stream=codec_type,width,height","-of","json",str(output)]))
    streams=probe.get("streams",[])
    video=next((s for s in streams if s.get("codec_type")=="video"),None)
    audio=next((s for s in streams if s.get("codec_type")=="audio"),None)
    if video is None:
        raise SystemExit("Final MP4 has no video stream")
    if audio is None:
        raise SystemExit("Final MP4 has no audio stream")
    if float(probe.get("format",{}).get("duration",0))<=0:
        raise SystemExit("Final MP4 has invalid duration")
    expected={"final_9x16.mp4":(1080,1920),"final_16x9.mp4":(1920,1080)}
    if output.name in expected and (video.get("width"),video.get("height"))!=expected[output.name]:
        raise SystemExit("Unexpected video dimensions: %sx%s" % (video.get("width"),video.get("height")))
    print("Validated %s: %sx%s, %s seconds" % (output,video["width"],video["height"],probe["format"]["duration"]))

if __name__=="__main__":
    main()
