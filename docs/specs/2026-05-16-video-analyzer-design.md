# video-analyzer — Design Spec

**Author:** Frank Nillard
**Date:** 2026-05-16
**Status:** Approved (post-review)

---

## 1. What we're building

A Python CLI tool and Claude Code skill that takes any video (URL or local file) and produces an `.avt` (Agentic Video Transcript) file. The .avt format is a hybrid document combining timestamped transcripts, AI-generated visual descriptions, and frame file references, designed for downstream agent consumption.

This is the foundation layer for the Idea Miner pipeline. It does NOT do evaluation or scoring. It produces structured, agent-readable video breakdowns that other tools consume.

## 2. The .avt format

A new file format purpose-built for agentic video processing. Combines what was said (transcript), what was shown (visual descriptions), and raw evidence (frame files) into one document.

Full format specification lives in `docs/avt-spec.md`. Key rules:

- **All value lines are single-line only.** VISUAL, AUDIO, FRAME each occupy exactly one line.
- **AUDIO text uses single quotes** to avoid escaping issues: `AUDIO: 'transcript text here'`
- **Segments are separated by blank lines.** A new segment starts with a `[timestamp]` line.
- **Metadata ends at `---` separator.** The separator must be on its own line with nothing else.
- **Scene tags use a constrained vocabulary** (see Section 3.3).

### parse_avt() return schema

```python
{
    "version": "1.0",
    "metadata": {
        "title": str,
        "channel": str,
        "duration": str,          # HH:MM:SS
        "source": str,
        "analyzed": str,          # YYYY-MM-DD HH:MM:SS
        "model": str,
        "frames_extracted": int,
        "transcript_source": str  # captions|whisper-groq|whisper-openai|none
    },
    "segments": [
        {
            "start": str,         # MM:SS or HH:MM:SS
            "end": str,
            "scene": str,         # from constrained vocabulary
            "visual": str,        # single-line description
            "audio": str,         # transcript text (may be empty)
            "frame": str | None   # relative path to JPEG or None
        }
    ]
}
```

## 3. Architecture

```
Input: any video URL (yt-dlp supports 400+ sites) or local file

analyze.py (orchestrator)
  1. preflight.py   -> verify dependencies (yt-dlp, ffmpeg, API keys)
  2. download.py    -> fetch video locally via yt-dlp (or use local file)
  3. transcribe.py  -> get transcript (native captions preferred, Whisper fallback)
  4. understand.py  -> upload video to Gemini 2.5 Flash (structured JSON output)
  5. frames.py      -> extract JPEG frames at Gemini's identified timestamps
  6. avt.py         -> assemble .avt file from all outputs
  7. cleanup        -> delete temp video + Gemini uploaded file

Output: <video-slug>.avt + frames/ directory
```

### 3.1 Why Gemini for visual understanding

- Native video understanding (no frame extraction needed for the AI step)
- Sees motion, transitions, temporal flow, not just static snapshots
- Better at assessing production quality, charisma, pacing (needs temporal context)
- One API call vs 4-5 batched frame calls
- ~$0.05 per 10-minute video (Gemini 2.5 Flash)
- The model tells US where the key moments are, then we extract frames at those timestamps

### 3.2 Why we still extract frames

- The .avt FRAME references let downstream agents load actual images for deep analysis
- Cheap text-only pass for batch scanning (read VISUAL lines), full fidelity pass when needed (load FRAME files)
- Not every downstream consumer has video upload capability

### 3.3 Scene tag vocabulary (constrained)

```
intro, outro, hook, cta, sponsor
talking-head, screen-recording, demo, tutorial
slide, diagram, whiteboard, code
b-roll, montage, transition
interview, reaction, commentary
other
```

Tags are lowercase, hyphenated. Gemini prompt constrains output to this list. `other` is the catch-all.

### 3.4 Gemini constraints

- **Max file size:** 2 GB. Videos exceeding this are rejected before upload with a clear error.
- **Storage limit:** 20 GB across all uploaded files. We delete each file immediately after analysis.
- **File TTL:** Gemini deletes uploaded files after 48 hours. We don't rely on persistence.
- **Processing timeout:** Poll for ACTIVE state with 5-minute timeout. Fail if not ready.
- **Rate limits:** Free tier is 1000 req/day. Paid tier varies. We assume paid tier for production use.
- **Structured output:** Use `response_mime_type: "application/json"` with a defined schema to get deterministic, parseable responses.

### 3.5 Temp file policy

All temp files go to `~/.cache/video-analyzer/<run-id>/`:
- Downloaded video file
- Extracted audio (for Whisper)
- Intermediate data

**On success:** Temp dir is deleted. Only the .avt file and frames/ directory remain.
**On failure:** Temp dir is deleted via try/finally. Partial outputs are removed.
**Gemini cleanup:** Uploaded file is deleted via `files.delete()` in a finally block, regardless of success or failure.

The output frames/ directory is NOT temp — it persists alongside the .avt file as part of the output.

## 4. Scripts

### analyze.py (entry point / orchestrator)

CLI arguments:

| Flag | Default | Effect |
|---|---|---|
| `<source>` | required | Video URL or local file path |
| `--out-dir DIR` | current dir | Where to write .avt + frames/ |
| `--max-frames N` | 80 | Cap on extracted frames |
| `--no-whisper` | false | Disable Whisper fallback (frames-only if no captions) |
| `--whisper groq\|openai` | auto | Force specific Whisper backend |
| `--low-res` | false | Use 256px frame width (vs 512px default). Reduces output size. Does NOT affect Gemini analysis (video is uploaded at original quality). |

- Orchestrates the full pipeline: preflight, download, transcribe, understand, extract frames, assemble .avt
- Prints progress to stderr, final .avt path to stdout
- Wraps entire pipeline in try/finally for cleanup
- Rejects videos over 2 GB before uploading to Gemini
- Rejects videos over 90 minutes with a warning (user can override with `--force-long`)

### download.py (video acquisition)

- Wraps yt-dlp for URL sources
- Passes through local file paths directly
- Returns: video file path, subtitle path (if available), video metadata (title, uploader, duration)
- Supports 400+ sites via yt-dlp
- **Error handling:** Age-restricted, private, members-only, DRM-protected videos fail fast with a clear message. No retries on auth failures.

### transcribe.py (transcript extraction)

- First attempts native captions via yt-dlp (free, preferred)
- Falls back to Whisper API if no captions: Groq whisper-large-v3 (preferred) or OpenAI whisper-1
- Parses VTT format into timestamped segments
- **VTT cleanup:** Strips HTML tags (`<c>`, `<b>`, etc.), deduplicates adjacent identical cues (YouTube rolling captions), normalizes whitespace
- **No audio detection:** If extracted audio is silence (< 1 second of speech detected), returns empty segments with transcript_source "none" instead of sending to Whisper
- Returns: list of {start, end, text} segments, transcript source label

### whisper.py (Whisper API clients)

- Groq and OpenAI Whisper client implementations
- Loads API keys from ~/.config/video-analyzer/.env
- Audio extraction via ffmpeg (mono 16kHz, ~0.5MB/min)

### understand.py (Gemini video understanding)

- Uploads video to Gemini Files API
- Polls until ACTIVE state (5-minute timeout, fail if exceeded)
- Uses **structured output mode** (`response_mime_type: "application/json"`) with this schema:

```json
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "start": {"type": "string", "description": "MM:SS or HH:MM:SS"},
      "end": {"type": "string", "description": "MM:SS or HH:MM:SS"},
      "visual": {"type": "string", "description": "1-2 sentence description of what is on screen"},
      "scene": {"type": "string", "enum": ["intro","outro","hook","cta","sponsor","talking-head","screen-recording","demo","tutorial","slide","diagram","whiteboard","code","b-roll","montage","transition","interview","reaction","commentary","other"]}
    },
    "required": ["start", "end", "visual", "scene"]
  }
}
```

- Prompt template (stored in `scripts/prompts/understand.txt`):

```
Analyze this video and identify all key visual moments. For each distinct visual segment, provide:
- start: timestamp when this segment begins (MM:SS format)
- end: timestamp when this segment ends (MM:SS format)
- visual: 1-2 sentence description of what is shown on screen. Focus on: environment/setup, screen content, people visible, text on screen, production quality indicators.
- scene: one tag from this list: intro, outro, hook, cta, sponsor, talking-head, screen-recording, demo, tutorial, slide, diagram, whiteboard, code, b-roll, montage, transition, interview, reaction, commentary, other

Return ONLY the JSON array. Aim for segments of 3-30 seconds each. Capture every meaningful visual change.
```

- **Cleanup:** Deletes uploaded file via `client.files.delete()` in finally block.
- Requires: GOOGLE_API_KEY in .env

### frames.py (frame extraction)

- Takes list of timestamps from understand.py
- Extracts JPEG frames at exactly those timestamps via ffmpeg
- **No fallback path.** If understand.py fails, the pipeline fails. Scene detection fallback removed to keep complexity down. (Can be added in a future version.)
- Configurable resolution: 512px wide (default) or 256px (--low-res)
- Caps at max frames (default 80). If Gemini returns more timestamps, takes evenly-spaced subset.
- Returns: list of {path, timestamp_seconds}

### avt.py (format assembler + parser)

- Takes: metadata dict, transcript segments, visual descriptions (from Gemini), frame paths
- Aligns transcript chunks to visual description time ranges
- Writes .avt file following the format spec in `docs/avt-spec.md`
- `write_avt(metadata, segments, output_path)` — writes the file
- `parse_avt(file_path) -> dict` — reads .avt back into the schema defined in Section 2
- Validates format version on parse. Rejects unknown versions.

### preflight.py (dependency checker) [renamed from setup.py]

- Verifies: ffmpeg, ffprobe, yt-dlp installed
- Checks API keys: GOOGLE_API_KEY (required), GROQ_API_KEY or OPENAI_API_KEY (optional, for Whisper)
- Auto-installs via brew on macOS if missing
- Scaffolds ~/.config/video-analyzer/.env with commented placeholders at 0600 permissions
- Exit codes: 0 (ready), 2 (missing binaries), 3 (missing API key), 4 (both)

## 5. Project structure

```
video-analyzer/
├── CLAUDE.md
├── requirements.txt             <- Python package dependencies
├── docs/
│   ├── PRD.md
│   ├── scratchpad.md
│   ├── avt-spec.md
│   └── specs/
│       └── 2026-05-16-video-analyzer-design.md
├── activity.md
├── scripts/
│   ├── analyze.py
│   ├── download.py
│   ├── frames.py
│   ├── transcribe.py
│   ├── whisper.py
│   ├── understand.py
│   ├── avt.py
│   ├── preflight.py
│   └── prompts/
│       └── understand.txt       <- Gemini prompt template
├── commands/
│   └── analyze.md
├── SKILL.md
├── LICENSE
├── README.md
└── .gitignore
```

## 6. Configuration

API keys stored in `~/.config/video-analyzer/.env`:

```
GOOGLE_API_KEY=...          # Required — Gemini 2.5 Flash for video understanding
GROQ_API_KEY=...            # Optional — Whisper transcription (preferred)
OPENAI_API_KEY=...          # Optional — Whisper transcription (fallback)
```

Python dependencies in `requirements.txt`:
```
google-genai>=1.0.0
httpx>=0.27.0
python-dotenv>=1.0.0
```

Install: `pip install -r requirements.txt` (inside a venv recommended).

## 7. MVP scope

### In scope
- Single video analysis: one URL or local file path -> one .avt file + frames/
- Video download from any yt-dlp-supported site (400+)
- Transcript extraction (captions or Whisper fallback)
- Gemini 2.5 Flash video understanding with structured JSON output
- Frame extraction at Gemini-identified key moments
- .avt file generation and parsing
- /analyze command for Claude Code
- Dependency checker and setup wizard
- Temp file cleanup on success and failure

### Out of scope (future projects)
- Batch processing (multiple URLs in one run)
- Outlier discovery (YouTube API integration)
- 11-parameter SOP evaluation layer
- Idea extraction and scoring
- Web API / dashboard interface
- Hermes/OpenClaw deployment
- Scene detection fallback (ffmpeg-based)

### Known unsupported inputs
- Age-restricted videos (require browser cookies — fail fast with message)
- Private/unlisted videos (require auth — fail fast)
- Members-only videos (require channel cookies — fail fast)
- DRM-protected content (Netflix, Disney+, etc. — fail fast)
- Live streams (unbounded length — rejected unless under 90 min)

## 8. Dependencies

System:
- Python 3.11+
- yt-dlp (`brew install yt-dlp`)
- ffmpeg / ffprobe (`brew install ffmpeg`)

Python packages (in requirements.txt):
- google-genai (Gemini API client)
- httpx (HTTP requests)
- python-dotenv (env file loading)

## 9. Cost model

Token calculation: ~263 tokens/second of video (Gemini docs: 258 tokens/frame at 1fps + 32 tokens/sec audio). Gemini 2.5 Flash pricing: $0.30/M input tokens, $2.50/M output tokens (as of May 2026).

| Video length | Seconds | Input tokens | Input cost | Output (~2K) | Total |
|---|---|---|---|---|---|
| 5 min | 300 | ~79K | $0.024 | $0.005 | ~$0.03 |
| 10 min | 600 | ~158K | $0.047 | $0.005 | ~$0.05 |
| 20 min | 1200 | ~316K | $0.095 | $0.005 | ~$0.10 |

Pricing subject to change. Check ai.google.dev/pricing for current rates.

## 10. Success criteria

Run `/analyze <any-video-url>` and get:
1. A valid .avt file with metadata, timestamped transcript, visual descriptions, scene tags, and frame references
2. A frames/ directory with JPEGs extracted at key moments identified by Gemini
3. Completion under 2 minutes for a 10-minute video on fast connection with native captions. Under 5 minutes in typical conditions (includes upload time for large files).
4. `avt.parse_avt()` reads the .avt file back into the dict schema from Section 2
5. Temp files cleaned up. No downloaded video or Gemini file lingering after run.

## 11. Build batches

| Batch | Deliverables | Depends on |
|---|---|---|
| B1: Foundation | preflight.py, download.py, transcribe.py, whisper.py, requirements.txt | Nothing |
| B2: Intelligence | understand.py, prompts/understand.txt | B1 (needs download.py) |
| B3: Extraction | frames.py | B2 (needs Gemini timestamps) |
| B4: Format | avt.py (writer + parser) | B1 + B2 + B3 |
| B5: Orchestration | analyze.py, SKILL.md, commands/analyze.md | All above |
| B6: Polish | README.md, end-to-end test on real video | B5 |

## 12. Review resolutions

Issues from spec review (2026-05-16) and how they were addressed:

| ID | Issue | Resolution |
|---|---|---|
| C1 | .avt parser ambiguity | Single-line values only, single quotes for AUDIO, blank line separators, parse_avt() schema defined |
| C2 | Gemini Files API limits | Section 3.4 added: 2GB gate, 5min timeout, delete-after-use, rate limit notes |
| C3 | No temp file cleanup | Section 3.5 added: dedicated cache dir, try/finally cleanup, Gemini file deletion |
| I1 | Gemini prompt underspecified | Structured JSON output schema defined, prompt template specified, scene tags constrained |
| I2 | Edge-case video types | Section 7 "Known unsupported inputs" added, 90-min guard for live streams |
| I3 | Cost model token math | Corrected with formula: 263 tokens/sec. Figures updated. |
| I4 | Build batch dependency gap | Scene detection fallback removed. frames.py hard-requires Gemini timestamps. |
| I5 | --low-res undefined | Flag table added to Section 4. Affects frame width only (256px vs 512px). |
| I6 | setup.py naming conflict | Renamed to preflight.py throughout. |
| M1 | VTT dedup/tag stripping | Added to transcribe.py spec: strip HTML, dedup rolling captions. |
| M2 | .avt MIME type | Deferred to post-MVP. Use text/plain for now. |
| M3 | Success criteria timing | Split into fast-path (2 min) and typical (5 min) scenarios. |
| M4 | .gitignore missing | Already created in project. |
| M5 | No requirements.txt | Added to project structure and B1 batch. |
