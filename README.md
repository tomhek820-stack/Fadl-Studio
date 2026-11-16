# Fadl Studio

خط إنتاج عربي لإنشاء فيديوهات قصيرة قابلة للنشر من فكرة أو نص، باستخدام Remotion وPiper TTS وFFmpeg.

## المتطلبات
- Node.js 22 أو أحدث.
- Python 3.11 أو أحدث.
- FFmpeg وFFprobe.
- اتصال إنترنت أول مرة لتنزيل نموذج الصوت العربي من Hugging Face.

## إنشاء فيديو المحتوى الاجتماعي

~~~bash
npm install
python3 -m pip install piper-tts==1.3.0
python3 scripts/build_demo.py
~~~

الملفات الناتجة:
- demo/output/final_9x16.mp4 — عمودي 1080×1920، مناسب لـ Reels وShorts وTikTok.
- demo/output/final_16x9.mp4 — أفقي 1920×1080.

## الصوت والترجمة كلمة بكلمة
- حرر الفكرة والمشاهد والتعليق الصوتي في demo/scenes.json.
- السرعة الافتراضية 1.08 (أسرع بنحو 8%) مع FFmpeg atempo.
- تُقاس مدة WAV بعد تغيير السرعة، ثم تُحسب نوافذ ظهور الكلمات.
- تظهر الكلمات تدريجيًا، وتُميّز الكلمة الحالية بلون واضح.
- توقيت الكلمات تقديري موزع بحسب طول الكلمات وعلامات الوقف؛ يجب مراجعته بصريًا وسمعيًا قبل النشر، ولا يُعد محاذاة صوتية دقيقة.
- راجع pronunciation.md للأسماء والمصطلحات.

## المقاسات
Remotion يتضمن 9:16 و16:9 و1:1 و4:5. مهمة التسليم الحالية تصدر 9:16 و16:9.

## الفحوص
~~~bash
npm run typecheck
npm test
python3 scripts/build_demo.py
~~~

GitHub Actions يبني الفيديو ويرفع MP4 وتقرير الجودة كـ Artifact.

## التراخيص
راجع THIRD-PARTY-NOTICES.md قبل النشر التجاري. لا يحتاج مسار الصوت المحلي إلى مفتاح API.
