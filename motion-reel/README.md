Fadl Studio — Motion Reel

مسار مستقل صامت لمدة 40 ثانية، 1080x1920، 30fps، 1200 إطارًا.

التشغيل:
cd motion-reel
npm install
# ثبت ffmpeg وffprobe
npm run build

الناتج: output/reel.mp4 و QUALITY_REPORT.md.

المكونات: beats.json للستوري بورد؛ engine.js لمحرك Canvas الحتمي وsetTime(t)؛ index.html للمعاينة والسحب؛ render.mjs لتصدير PNG ثم MP4؛ verify.mjs لبوابة FFprobe والحتمية والنصوص.

كل الأصول مرسومة بالكود. Alexandria محلي من @fontsource. لا صور خارجية ولا API ولا تعليق أو موسيقى. علامتا Claude وMutqin مؤقتتان.
