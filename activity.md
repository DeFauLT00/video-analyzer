# video-analyzer — Activity Log

## Session 1 — 2026-05-16

### What was completed
- Brainstormed full project scope: video analysis toolkit producing .avt files
- Researched Brad's claude-video skill (MIT, Python, yt-dlp + ffmpeg + Whisper)
- Designed .avt format (Agentic Video Transcript): hybrid text descriptions + frame references
- Decided on Gemini 2.5 Flash for native video understanding (vs Claude Vision on frames)
- Designed smart frame extraction: Gemini identifies key moments, ffmpeg extracts at those timestamps
- Researched Gemini pricing: ~$0.06 per 10-minute video
- Wrote design spec
- Set up project harness (CLAUDE.md, PRD, scratchpad, activity log)

### Decisions made
- Gemini over Claude Vision for video understanding (temporal context, cheaper, one API call)
- Hybrid .avt format (text + frame refs) over pure text or pure images
- Smart extraction over even-spaced frames
- Project name: video-analyzer
- Folder: video_understanding (under Frank Projects)

### Lessons learned
- Native video understanding models (Gemini) are fundamentally better for temporal analysis than frame-by-frame vision API calls
- The .avt format solves the "lossy text vs expensive images" tradeoff with a two-pass approach
