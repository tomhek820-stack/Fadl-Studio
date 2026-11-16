# AGENTS.md — Fadl Studio

## Project goal
Build a reliable Arabic-first video production pipeline that turns an Arabic idea or script into polished social videos with narration, RTL typography, word-synchronized captions and MP4 exports.

## Arabic language and typography
- Use clear Modern Standard Arabic in visible copy unless a dialect is explicitly requested.
- Set RTL explicitly for every Arabic text layer and caption.
- Use Noto Sans Arabic; Cairo, Tajawal or IBM Plex Sans Arabic may be introduced only with license notices.
- Prevent disconnected glyphs, accidental English labels, mirrored punctuation and clipped diacritics.
- Review names, acronyms and numbers before speech generation.

## Pronunciation and captions
- Use one consistent Arabic voice throughout a video.
- Split narration into short scene-sized sentences.
- Maintain pronunciation.md for difficult words.
- Measure generated WAV duration after any speed change.
- Prefer true forced alignment when an available model/tool can run reliably. If using estimated word timings, disclose that limitation in the quality report and require human review.
- Reveal caption words progressively and highlight the currently spoken word.
- Never claim word-perfect synchronization based only on character-weighted estimates.
- Listen to the final audio before claiming pronunciation quality.

## Video
- Use Remotion for scenes, typography, motion and captions.
- Use FFmpeg for audio processing and final encoding; preserve pitch as much as possible when adjusting speech speed.
- Target at least 1080p. Presets: 9:16 (1080×1920), 16:9 (1920×1080), 1:1 (1080×1080), 4:5 (1080×1350).
- Produce social-first hooks, clear value and a concise call to action when the brief is for social publishing.
- Include captions synchronized to measured speech timing.

## Security and licensing
- Never commit API keys, credentials or access tokens.
- Use environment variables or GitHub Secrets for optional hosted services.
- Do not silently change license files, dependency versions or workflow permissions.
- Download voice models on demand; do not commit large model binaries.
- Check model and training-data licensing separately.

## Tests and quality gates
- Run type checks and tests after changes.
- Verify RTL visually in rendered frames.
- Verify audio duration and every caption timing interval.
- Verify exported MP4 streams, dimensions and duration with FFprobe.
- Report estimated alignment honestly; automated tests do not replace human listening and visual review.
