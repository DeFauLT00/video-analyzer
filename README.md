# video-analyzer

Analyze any video and produce an `.avt` (Agentic Video Transcript) file — a structured, plain-text format designed for AI agent consumption.

Takes any video URL (YouTube, Vimeo, X, TikTok, 400+ sites) or local file and produces a document combining timestamped transcripts, AI-generated visual descriptions, scene tags, and extracted frame references.

```
Input:  Any video URL or local file
Output: video-slug.avt + frames/ directory
```

## Install as a Claude Code Skill (Recommended)

The easiest way to use video-analyzer. No manual setup required.

**1. Add the skill** — In Claude Code, add this repository URL as a skill source:

```
https://github.com/docusphere/video-analyzer
```

**2. Run it** — From any project, type:

```
/analyze https://youtube.com/watch?v=VIDEO_ID
```

**3. That's it** — On first run, Claude will automatically:
- Install Python dependencies
- Install ffmpeg and yt-dlp (macOS with Homebrew)
- Ask for your Gemini API key and save it securely
- Run the analysis and present results

You'll need a free Gemini API key. Get one at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

## What you get

The `.avt` format gives AI agents everything they need to understand a video without watching it:

- **VISUAL** — AI-generated description of what's on screen
- **AUDIO** — Timestamped transcript of what's being said
- **FRAME** — Extracted JPEG frame for deep visual analysis
- **Scene tags** — Content type classification (intro, demo, talking-head, screen-recording, etc.)

### Example output

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

1. **Download** — yt-dlp fetches the video (supports 400+ sites via yt-dlp)
2. **Transcribe** — Native captions extracted first, Whisper API fallback if none available
3. **Understand** — Video uploaded to Gemini 2.5 Flash for native video understanding (not frame-by-frame — the model sees the actual video)
4. **Extract** — JPEG frames pulled at AI-identified key moments via ffmpeg
5. **Assemble** — Everything combined into the `.avt` format

## Cost

- **Gemini 2.5 Flash:** ~$0.05 per 10-minute video
- **Whisper (only if no captions):** ~$0.01/minute of audio
- Most YouTube videos have native captions, so Whisper is rarely needed

## Standalone CLI Usage

You can also run video-analyzer directly without Claude Code.

### Prerequisites

- Python 3.11+
- ffmpeg and yt-dlp (`brew install ffmpeg yt-dlp` on macOS)
- Gemini API key

### Setup

```bash
git clone https://github.com/docusphere/video-analyzer.git
cd video-analyzer
pip install -r requirements.txt
python3 scripts/preflight.py  # checks deps + scaffolds config
```

Add your Gemini API key to `~/.config/video-analyzer/.env`:

```
GOOGLE_API_KEY=your-key-here
```

Optional keys for Whisper transcription fallback:
```
GROQ_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
```

### Run

```bash
python3 scripts/analyze.py https://youtube.com/watch?v=VIDEO_ID
```

### CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `<source>` | required | Video URL or local file path |
| `--out-dir DIR` | `.` | Output directory |
| `--max-frames N` | 80 | Maximum frames to extract |
| `--no-whisper` | false | Disable Whisper fallback |
| `--whisper groq\|openai` | auto | Force Whisper backend |
| `--low-res` | false | 256px frames (vs 512px default) |
| `--force-long` | false | Allow videos over 90 minutes |

## License

Copyright (c) 2026 Frank Nillard. Source-Available (Non-Commercial).

Free for personal and educational use. Commercial use requires written permission. See [LICENSE](LICENSE) for full terms.
