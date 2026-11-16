# Third-party notices

- **Remotion 4.0.534**: governed by the Remotion License, not an OSI-approved open-source license. Review current eligibility and terms at https://www.remotion.dev/docs/license before commercial deployment.
- **FFmpeg**: LGPL 2.1+ by default, with optional GPL components. The GitHub runner binary configuration governs the actual binary. See https://ffmpeg.org/legal.html.
- **Piper TTS engine 1.3.0**: GPL-3.0-or-later. The project invokes the installed engine as a separate local process and does not bundle its runtime into this repository. Review redistribution obligations before shipping a combined distribution. See https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/LICENSING.md.
- **Piper Arabic Kareem medium voice**: downloaded on demand from https://huggingface.co/rhasspy/piper-voices. Its model card says the Arabic dataset license must be checked at the linked source and that the voice was fine-tuned from the U.S. English Lessac medium voice. The upstream Piper licensing guidance warns that Lessac-derived voices may carry non-commercial restrictions. Do not use this voice for commercial publishing or redistribute its weights until the complete training-chain rights are confirmed.
- **Noto Sans Arabic**: SIL Open Font License 1.1; see https://github.com/google/fonts/tree/main/ofl/notosansarabic.

No third-party model weights or API credentials are committed to this repository.
\n- **Google Cloud Text-to-Speech Chirp 3 HD** (optional): accessed through the Google Cloud Text-to-Speech API when GOOGLE_TTS_API_KEY is configured. Billing, API terms, and voice availability apply. The current demo uses ar-XA-Chirp3-HD-Charon; verify current Google Cloud terms before commercial distribution.\n