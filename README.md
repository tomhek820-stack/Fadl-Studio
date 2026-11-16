# Fadl Studio

خط إنتاج عربي لإنشاء فيديوهات قصيرة قابلة للنشر من فكرة أو نص، باستخدام Remotion وMicrosoft Edge Neural TTS (مجاني) مع Piper كخيار احتياطي دون اتصال وFFmpeg.

## المتطلبات
- Node.js 22 أو أحدث.
- Python 3.11 أو أحدث.
- FFmpeg وFFprobe.
- اتصال إنترنت أثناء البناء لتنزيل الأدوات والنماذج.
- اتصال إنترنت لتوليد الصوت عبر Edge Neural TTS؛ لا يحتاج مفتاح API أو حسابًا مدفوعًا. يعمل Piper كخيار احتياطي محلي.

## إنشاء فيديو المحتوى الاجتماعي

~~~bash
npm install
python3 -m pip install edge-tts piper-tts==1.3.0
python3 scripts/build_demo.py
~~~

الملفات الناتجة:
- demo/output/final_9x16.mp4 — عمودي 1080×1920، مناسب لـ Reels وShorts وTikTok.
- demo/output/final_16x9.mp4 — أفقي 1920×1080.

## الصوت والترجمة كلمة بكلمة
- حرر النص في demo/scenes.json.
- يُنتج التعليق الصوتي كله في ملف WAV واحد، فلا يعاد تشغيل محرك الصوت عند كل مشهد ولا تنقطع النبرة عند الانتقال.
- عند إضافة سر المستودع GOOGLE_TTS_SERVICE_ACCOUNT_JSON (محتوى ملف حساب خدمة Google بصيغة JSON)، يستخدم Gemini 3.1 Flash TTS Preview باللغة العربية العامة ar-001 وصوت Charon مع تعليمات أداء بشري طبيعي.
- يلزم تفعيل Cloud Text-to-Speech API وVertex AI API ومنح حساب الخدمة دور Vertex AI User.
- إذا لم يتوفر السر، يستخدم Piper كخيار احتياطي في استدعاء صوتي واحد.
- لا نسرّع الصوت بعد التوليد؛ السرعة الطبيعية 1.0 تحافظ على الوقفات والتنغيم.
- تظهر الكلمات تدريجيًا وتُميّز الكلمة الحالية. توقيت الكلمات وحدود المشاهد تقديري وليس محاذاة صوتية دقيقة؛ يجب تدقيقه قبل النشر.
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
راجع THIRD-PARTY-NOTICES.md قبل النشر التجاري. لا يحتاج مسار Piper المحلي إلى مفتاح API. يتطلب Gemini TTS إعداد Google Cloud وحساب خدمة، وقد تُطبق رسوم الاستخدام.
