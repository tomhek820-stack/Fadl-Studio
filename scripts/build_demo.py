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

def main():
    OUT.mkdir(parents=True,exist_ok=True)
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
    report="""# تقرير جودة الفيديو التجريبي

## الحالة
اكتمل التوليد والبناء والتصدير آليًا. يلزم الاستماع والمراجعة البصرية البشرية قبل النشر.

## الأدوات
- Remotion 4.0.534 للمشاهد والحركة والنصوص والكابشن.
- Piper TTS بالصوت العربي {voice} للتوليد المحلي دون مفتاح API.
- FFmpeg لترميز H.264/AAC وتطبيع مستوى الصوت، وFFprobe للتحقق من الملف.
- Noto Sans Arabic للعرض العربي.

## الملفات
- السيناريو: demo/scenes.json
- بيانات الصوت والتوقيت: demo/generated/metadata.json
- ملف الخصائص: demo/generated/props.json
- الفيديو العمودي: demo/output/final_9x16.mp4
- الفيديو الأفقي: demo/output/final_16x9.mp4

## المدة
- المدة المحسوبة من ملفات WAV مع فاصل قصير بين المشاهد: {duration:.2f} ثانية.
- تفاصيل المشاهد: {scenes}

## جودة الصوت والمزامنة
- الصوت: ملف WAV مستقل لكل مشهد، بصوت واحد ثابت.
- التوقيت: محسوب من عدد إطارات WAV الفعلي؛ لا يجري قص الجمل لتناسب مدة ثابتة.
- الكابشن: نص المشهد ظاهر خلال تسلسل الصوت نفسه.
- يلزم الاستماع البشري للتأكد من جودة النطق والأسماء والوقفات.

## التحقق
- اجتاز TypeScript وفحوص Python قبل التصيير.
- اجتاز FFprobe التحقق من وجود مساري الفيديو والصوت ومدة موجبة لكل ملف نهائي.
- راجع أبعاد كل ملف عبر ffprobe قبل النشر.

## مشكلات وقيود متبقية
- صوت Piper متوسط الجودة وبلهجة أردنية؛ قد يحتاج بعض المصطلحات والأسماء إلى ضبط في pronunciation.md.
- ترخيص بيانات التدريب المشار إليها في بطاقة النموذج يحتاج مراجعة مستقلة قبل الاستخدام التجاري.
- يجب مراجعة RTL بصريًا والاستماع إلى الفيديو النهائي على جهاز فعلي.

## إعادة التشغيل
1. ثبّت piper-tts==1.3.0.
2. شغّل npm install.
3. شغّل python3 scripts/build_demo.py.
""".format(voice=metadata["voice"],duration=metadata["durationSeconds"],scenes=json.dumps(metadata["scenes"],ensure_ascii=False))
    (ROOT/"demo/quality-report.md").write_text(report,encoding="utf-8")
    print("Build complete. See demo/quality-report.md")

if __name__=="__main__":
    main()
