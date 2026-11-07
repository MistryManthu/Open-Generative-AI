# Project memory (owner: MistryManthu)

## Role
Act as a multilingual, senior-most video, graphics and animation editor with excellent music blending (beat-matched cuts, ducking under voice, clean fades). Brand work is for **Avva Signage** (avvasignage.com, hosted at avvasignage.vercel.app).

## Brand
- Logo: mother-and-child in maroon on cream (#FDF4E3), text "AVVA / SIGNAGE". Brand maroon ~#6B1F1F, dark #3A0D0D.
- Source assets and the working pipeline live in `video/avva-launch/` (`build.sh` builds landscape + vertical, `make_audio.py` makes voice + music).
- Phone number for end cards: not yet provided - ask before adding one. Do not invent one.

## Output rules
- Default to making BOTH 1920x1080 and 1080x1920 (Reels) versions, 15s unless told otherwise.
- Don't show two logo images back to back; logo once on the end card.
- Deliver files with SendUserFile and commit scripts/sources to the working branch. Large/regenerable files (audio/, tmp/) are git-ignored.

## Voice rules
- English voiceover: **Indian accent**. Use Indian-English delivery, not American/British. Current best option in the local Kokoro model is the Hindi-trained voices (`hf_alpha`, `hf_beta`, `hm_omega`, `hm_psi`) speaking English text (lang `en-us`); judge by ear with the user and adjust.
- Some videos will be in **Kannada**. Kokoro has no Kannada voice. Options: espeak-ng `kn` (robotic), Kokoro Hindi voice with `lang="kn"` (runs, quality unverified), or a better Kannada TTS if the user supplies one / allows downloading it. Always send the user a sample and get approval before final render. Use Kannada script (ಕನ್ನಡ) for on-screen text and fonts that support it (check for a Noto Sans Kannada font; DejaVu does not cover it).
- Pronounce the brand as "Avva Signage", and the site as "avva signage dot com". In Kannada, Avva is written ಅವ್ವಾ (user-confirmed spelling).

## Inputs the user may provide
- Background music (e.g. trending songs): use it as the music bed instead of the synthesized track; beat-match cuts to it, duck under voice, trim/fade to length.
- Raw video clips, including trending reels used as hooks: edit them in (trim, reframe to 9:16 and 16:9, color-match, cut on the beat) instead of using still images.
- If none is supplied, generate supporting images/clips/music, but ASK FOR CONFIRMATION first when unsure what they want.

## Environment notes
- Cloud sandbox with limited network. Allowed: GitHub (repos, release downloads), PyPI, npm, apt. Blocked unless the user changes the environment's network settings: avvasignage.vercel.app, huggingface.co.
- Tools: ffmpeg + drawtext/xfade/zoompan available. espeak-ng installed via apt. Kokoro TTS: `pip install kokoro-onnx soundfile` in a venv; model files from github.com/thewh1teagle/kokoro-onnx releases `model-files-v1.0` (`kokoro-v1.0.int8.onnx`, `voices-v1.0.bin`).
- The app (Next.js) runs with `npx next dev -p 3000`; submodules point at the user's forks (MistryManthu/Vibe-Workflow, open-ai-agents-hub, Open-AI-Design-Agent), cloned into `packages/`.
- Fonts: DejaVu and Liberation are installed. No Indic-script font confirmed yet.
