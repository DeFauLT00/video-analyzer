# video-analyzer — Product Requirements Document

## What it is
A Python CLI tool and Claude Code skill that takes any video (URL or local file) and produces a structured .avt (Agentic Video Transcript) file. The .avt format combines timestamped transcripts, AI-generated visual descriptions, and frame file references into a single agent-readable document.

## Why it exists
Current video analysis requires either watching the video manually or feeding raw frames + transcripts to an AI model, which is expensive and loses temporal context. The .avt format creates a reusable, searchable, agent-consumable representation of any video that can be processed by any downstream tool without re-watching.

## User type
Single user: Frank Nillard. Used directly via CLI or Claude Code /analyze command.

## Full vision
1. Analyze any video source into .avt format (MVP)
2. Batch processing of multiple videos
3. 11-parameter SOP evaluation layer (reads .avt files)
4. Outlier discovery pipeline (YouTube API)
5. Idea extraction and scoring
6. Autonomous execution via Hermes on VPS

## MVP scope
- Single video analysis only
- Input: one URL (400+ sites via yt-dlp) or one local file path
- Output: one .avt file + frames/ directory
- Gemini 2.5 Flash for video understanding
- Captions or Whisper for transcript
- /analyze command for Claude Code

## Data model
No database. File-based output:
- `.avt` file (plain text, custom format)
- `frames/` directory (JPEG files)
- Config: `~/.config/video-analyzer/.env`

## What's explicitly out of scope
- Web UI / dashboard
- Database / storage layer
- Multi-video batch runs
- Evaluation / scoring
- Any deployment infrastructure
- User authentication (single user, local only)

## Done definitions
- /analyze <youtube-url> produces a valid .avt file
- /analyze <local-file> produces a valid .avt file
- .avt file contains: metadata header, timestamped transcript, visual descriptions, scene tags, frame references
- frames/ directory contains JPEGs at key moments
- avt.parse_avt() can read any .avt file back into structured data
- Setup wizard handles missing deps and API keys
- Completes in under 2 minutes for a 10-minute video
