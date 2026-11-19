#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"demo/output"
GEN=ROOT/"demo/generated"

def run(args):
    print("+"," ".join(args),flush=True)
    subprocess.run(args,cwd=ROOT,check=True)

def validate_source():
    source=json.loads((ROOT/"demo/scenes.json").read_text(encoding="utf-8"))
    scenes=source.get("scenes",[])
    if len(scenes) != 5:
        raise RuntimeError("Expected exactly five scenes")
    if source.get("speechSpeed") != 1:
        raise RuntimeError("Speech speed must remain 1.0; artificial speed-up is forbidden")
    required={"id","eyebrow","title","body","narration","caption","icon"}
    for index,scene in enumerate(scenes,1):
        missing=required-set(scene)
        if missing:
            raise RuntimeError(f"Scene {index} is missing fields: {sorted(missing)}")
        if not scene["narration"].strip() or scene["narration"] != scene["caption"]:
            raise RuntimeError(f"Scene {index} narration/caption mismatch or empty narration")
        if len(scene["narration"]) > 180:
            raise RuntimeError(f"Scene {index} narration exceeds 180 characters")
    print("Source preflight passed: five scenes, matching captions, normal speech speed.")

def main():
    validate_source()
    OUT.mkdir(parents=True,exist_ok=True)
    run([sys.executable,"scripts/download_visual_assets.py"])
    run([sys.executable,"scripts/generate_demo.py"])
    run(["npm","run","typecheck"])
    run(["npm","test"])
    for composition,temp,final in [
      ("DemoVertical",OUT/".rendered_9x16.mp4",OUT/"final_9x16.mp4"),
      ("DemoLandscape",OUT/".rendered_16x9.mp4",OUT/"final_16x9.mp4")]:
        run(["npx","remotion","render","src/index.tsx",composition,str(temp),
          "--props="+str(GEN/"props.json"),"--codec=h264","--pixel-format=yuv420p","--concurrency=1"])
        run([sys.executable,"scripts/finalize_video.py",str(temp),str(final)])
        temp.unlink(missing_ok=True)
    metadata=json.loads((GEN/"metadata.json").read_text(encoding="utf-8"))
    details=json.loads((GEN/"props.json").read_text(encoding="utf-8"))["scenes"]
    scene_lines="\n".join(
      "- {id}: {frames} إطارًا للكلام، {words} كلمة".format(
        id=s["id"],frames=s["audioDurationFrames"],words=s["wordCount"])
      for s in metadata["scenes"])
    report=f"""# تقرير جودة فيديو المحتوى الاجتماعي

## الحالة
نجح توليد الصوت والتصيير والتصدير الآلي. يلزم الاستماع والمراجعة البصرية البشرية قبل النشر.

## مواصفات المحتوى
- العنوان: {json.loads((ROOT/"demo/scenes.json").read_text(encoding="utf-8"))["title"]}
- النوع: فيديو قصير بخطاف افتتاحي وفائدة عملية ودعوة للمتابعة.
- محرك الصوت: {metadata["voice"]}.
- مدة مسار التعليق الصوتي المتصل: {metadata["audioDurationSeconds"]:.2f} ثانية؛ لا يوجد تسريع لاحق للصوت.
- نمط الترجمة: إظهار تدريجي للكلمات مع تمييز الكلمة الحالية.
- دقة التوقيت: تقدير موزون بطول الكلمات وعلامات الوقف نسبةً إلى مدة ملف WAV؛ ليست محاذاة صوتية على مستوى الفونيم، لذلك يلزم فحص بشري وضبط عند الحاجة.

## الأدوات
- Remotion للمشاهد والحركة والترجمة المتحركة.
- Microsoft Edge Neural TTS المجاني كمحرك أول، وPiper كخيار احتياطي محلي عند تعذر الاتصال.
- توليد التعليق الصوتي كاملاً في مسار WAV واحد لتجنب قطع النبرة عند انتقال المشاهد.
- FFmpeg لتوحيد معدل العينة والترميز النهائي، دون ضغط سرعة الكلام.
- Noto Sans Arabic للخط.
- FFprobe لفحص الصوت والصورة والأبعاد والمدة.

## ملفات التصدير
- demo/output/final_9x16.mp4 — 1080×1920.
- demo/output/final_16x9.mp4 — 1920×1080.

## مدة الفيديو
- المدة الإجمالية: {metadata["durationSeconds"]:.2f} ثانية.
- معدل الإطارات: 30 إطارًا في الثانية.
- تفاصيل الصوت:
{scene_lines}

## الفحوص
- TypeScript: يُشغّل قبل التصيير.
- اختبارات Python: تتحقق من السيناريو ومسار الصوت المتصل واستمرارية نطاقات توقيت الكلمات.
- FFprobe: يتحقق من مساري الصوت والصورة ومدة موجبة وأبعاد التصدير.
- الكابشن: كل كلمة تظهر عند بداية نافذتها الزمنية، وتُميّز الكلمة الحالية.

## ملاحظات الجودة والقيود
- تقدير توقيت الكلمات موزع بحسب طول الكلمة وعلامات الترقيم، وليس ناتج محاذاة forced-alignment؛ قد تنحرف بعض الكلمات عن النطق الطبيعي.
- يجب الاستماع إلى الصوت ومشاهدة المقطع كاملًا، خصوصًا توقيت الكلمات والأسماء والوقفات.
- المحرك الأساسي Edge Neural TTS المجاني بصوت عربي رجالي؛ عند تعذر الخدمة أو الاتصال يُستخدم Piper محليًا بصوت أردني متوسط الجودة. يتطلب Edge اتصالًا بالإنترنت وقد تتغير إتاحته.
- توقيت الكلمات وحدود المشاهد موزع تقديريًا على مدة الصوت؛ ليس محاذاة فونيمية دقيقة.
- راجع THIRD-PARTY-NOTICES.md قبل الاستخدام التجاري.

## إعادة التشغيل
~~~bash
npm install
python3 -m pip install edge-tts piper-tts==1.3.0
python3 scripts/build_demo.py
~~~
"""
    (ROOT/"demo/quality-report.md").write_text(report,encoding="utf-8")
    print("Build complete. See demo/quality-report.md")

if __name__=="__main__":
    main()
