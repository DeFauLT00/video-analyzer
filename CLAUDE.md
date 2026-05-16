# video-analyzer

Video analysis toolkit that produces .avt (Agentic Video Transcript) files from any video source. Foundation layer for the Idea Miner pipeline.

## Tech Stack
- Python 3.11+
- yt-dlp (video download, 400+ sites)
- ffmpeg/ffprobe (frame extraction, audio extraction)
- Gemini 2.5 Flash (native video understanding)
- Whisper API via Groq or OpenAI (transcript fallback)

## Commands
```bash
python3 scripts/analyze.py <url-or-path>          # analyze a video
python3 scripts/preflight.py --check                # verify dependencies
python3 scripts/preflight.py                        # install dependencies
```

## Architecture
```
analyze.py (orchestrator)
  -> preflight.py   (dependency check)
  -> download.py    (yt-dlp wrapper)
  -> transcribe.py  (captions or Whisper)
  -> understand.py  (Gemini video understanding)
  -> frames.py      (extract frames at key moments)
  -> avt.py         (assemble .avt file)
  -> cleanup        (temp files + Gemini uploaded file)
```

## Skill
- `/analyze <url-or-path>` — Claude Code skill in `.claude/skills/analyze/SKILL.md`

## Key Docs
- [Design Spec](docs/specs/2026-05-16-video-analyzer-design.md)
- [PRD](docs/PRD.md)
- [AVT Format Spec](docs/avt-spec.md)
- [Build Checklist](docs/scratchpad.md)

## Configuration
API keys in `~/.config/video-analyzer/.env`:
- `GOOGLE_API_KEY` (required) — Gemini 2.5 Flash
- `GROQ_API_KEY` (optional) — Whisper transcription (preferred)
- `OPENAI_API_KEY` (optional) — Whisper transcription (fallback)

## Conventions
- All scripts in `scripts/`. No nested packages.
- Entry point is always `analyze.py`.
- Output: `<video-slug>.avt` + `frames/` directory.
- Errors to stderr, results to stdout.
- No frameworks. Standard library where possible.

## Gotchas
- Gemini Files API needs polling — video processing is async.
- yt-dlp can fail on age-restricted/private/region-locked videos. Fail clearly, don't retry.
- Frame extraction depends on Gemini timestamps. If Gemini fails, the pipeline fails (no fallback).
- Never log or print API keys. Config file at 0600 permissions.
