# video-analyzer — Scratchpad

## Strategy
Build foundation scripts first (download, transcribe), then add intelligence layer (Gemini understanding), then wire everything through the .avt format. Test on a real video before polishing.

## Build Checklist

### B1: Foundation
- [ ] setup.py — dependency checker + installer
- [ ] download.py — yt-dlp wrapper
- [ ] transcribe.py — caption parsing + Whisper orchestration
- [ ] whisper.py — Groq/OpenAI Whisper clients

### B2: Intelligence
- [ ] understand.py — Gemini video upload + understanding

### B3: Extraction
- [ ] frames.py — extract frames at Gemini-identified timestamps (ffmpeg scene detection fallback)

### B4: Format
- [ ] avt.py — .avt assembler + parser
- [ ] docs/avt-spec.md — standalone format specification

### B5: Orchestration
- [ ] analyze.py — entry point orchestrator
- [ ] SKILL.md — skill contract
- [ ] commands/analyze.md — /analyze command

### B6: Polish
- [ ] README.md
- [ ] LICENSE
- [ ] .gitignore
- [ ] End-to-end test on real video
- [ ] Verify .avt parse round-trip

## Open Questions
- Gemini video upload size limit? Need to handle large files.
- Scene tag taxonomy — start with a small set and expand?
- Should .avt support multiple languages in transcript?

## Decisions
- 2026-05-16: Use Gemini 2.5 Flash for video understanding instead of Claude Vision on frames. Reason: native video understanding, temporal context, cheaper, one API call.
- 2026-05-16: Create hybrid .avt format with text descriptions + frame references. Reason: cheap scanning via text, deep dive via frames when needed.
- 2026-05-16: Smart frame extraction at Gemini-identified timestamps instead of even spacing. Reason: frames at moments that matter, not 80 screenshots of the same terminal.
