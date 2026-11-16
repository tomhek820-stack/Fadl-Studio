# Fadl Studio

Arabic-first video production pipeline built with Remotion, Piper TTS and FFmpeg.

The repository is being initialized with an editable 30-second Arabic demo. See `AGENTS.md` for engineering and Arabic typography rules once the feature branch is available.

## Planned workflow

1. Review and edit the Arabic scene script in `demo/scenes.json`.
2. Generate per-scene narration locally with Piper using the Arabic Jordanian Kareem medium voice.
3. Measure each WAV and create synchronized scene/caption metadata.
4. Render vertical, landscape, square and portrait compositions with Remotion.
5. Finalize MP4 files with FFmpeg.

No hosted speech API key is required. The voice model is downloaded on demand and is not committed to Git.
