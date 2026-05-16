---
name: analyze
description: Analyze any video URL or local file to produce an .avt (Agentic Video Transcript) file with visual descriptions, timestamped transcript, scene tags, and extracted key frames.
---

# /analyze

Analyze a video and produce a structured .avt file for agent consumption.

## Usage

```
/analyze <video-url-or-path>
```

## What it does

1. Downloads the video (supports 400+ sites via yt-dlp, or local files)
2. Extracts transcript (native captions preferred, Whisper fallback)
3. Uploads to Gemini 2.5 Flash for visual understanding
4. Extracts JPEG frames at AI-identified key moments
5. Assembles everything into a single .avt file

## Output

- `<video-slug>.avt` — Structured transcript with visual descriptions and scene tags
- `frames/` — JPEG frames at key visual moments

## Requirements

- ffmpeg, yt-dlp installed
- GOOGLE_API_KEY in ~/.config/video-analyzer/.env
- Optional: GROQ_API_KEY or OPENAI_API_KEY for Whisper fallback
