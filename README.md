# video-analyzer

Analyze any video and produce an `.avt` (Agentic Video Transcript) file — a structured, plain-text format designed for AI agent consumption.

Combines timestamped transcripts, AI-generated visual descriptions, scene tags, and extracted frame references into one parseable document.

## What it does

```
Input:  Any video URL (YouTube, Vimeo, 400+ sites) or local file
Output: video-slug.avt + frames/ directory
```

The `.avt` format gives AI agents everything they need to understand a video without watching it:
- **VISUAL** — What's on screen (AI-generated descriptions)
- **AUDIO** — What's being said (transcript)
- **FRAME** — Actual JPEG frame for deep analysis
- **Scene tags** — Content type classification (intro, demo, talking-head, etc.)

## Quick Start

### Prerequisites

- Python 3.11+
- ffmpeg (`brew install ffmpeg`)
- yt-dlp (`brew install yt-dlp`)
- Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### Install

```bash
git clone https://github.com/yourusername/video-analyzer.git
cd video-analyzer
pip install -r requirements.txt
python3 scripts/preflight.py  # checks + scaffolds config
```

### Configure

Add your API key to `~/.config/video-analyzer/.env`:

```
GOOGLE_API_KEY=your-key-here
```

Optional (for Whisper transcription fallback):
```
GROQ_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
```

### Run

```bash
python3 scripts/analyze.py https://youtube.com/watch?v=VIDEO_ID
```

Output: `video-title-slug.avt` + `frames/` in current directory.

## CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `<source>` | required | Video URL or local file path |
| `--out-dir DIR` | `.` | Output directory |
| `--max-frames N` | 80 | Maximum frames to extract |
| `--no-whisper` | false | Disable Whisper fallback |
| `--whisper groq\|openai` | auto | Force Whisper backend |
| `--low-res` | false | 256px frames (vs 512px default) |
| `--force-long` | false | Allow videos over 90 minutes |

## .avt Format

```
AGENTIC-VT 1.0

[metadata]
title: How I Built X With Claude Code
channel: Some Creator
duration: 08:36
source: https://youtube.com/watch?v=abc123
analyzed: 2026-05-16 14:30:00
model: gemini-2.5-flash
frames_extracted: 24
transcript_source: captions

---

[00:00 - 00:04] [scene:intro]
VISUAL: Man sitting at desk, ring light behind. Dark room setup.
AUDIO: 'What\'s up guys, today I want to show you something.'
FRAME: frames/frame-001.jpg

[00:04 - 00:15] [scene:screen-recording]
VISUAL: VS Code with Claude Code terminal in bottom panel.
AUDIO: 'The first thing you need to do is install this package.'
FRAME: frames/frame-002.jpg
```

Full format spec: [docs/avt-spec.md](docs/avt-spec.md)

## How it works

1. **Download** — yt-dlp fetches the video (supports 400+ sites)
2. **Transcribe** — Native captions extracted (Whisper API fallback)
3. **Understand** — Gemini 2.5 Flash analyzes the full video natively
4. **Extract** — Frames pulled at AI-identified key moments via ffmpeg
5. **Assemble** — Everything combined into the .avt format

## Cost

~$0.05 per 10-minute video (Gemini 2.5 Flash). Whisper adds ~$0.01/minute if no captions available.

## Claude Code Integration

This tool works as a Claude Code skill. Add it to your project and use:

```
/analyze <video-url>
```

## License

Copyright (c) 2026 Frank Nillard. MIT License.
