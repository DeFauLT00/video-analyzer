# Video Analyzer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI that takes any video URL or local file and produces an `.avt` (Agentic Video Transcript) file with timestamped transcripts, AI visual descriptions, scene tags, and extracted frame JPEGs.

**Architecture:** Orchestrator pattern — `analyze.py` calls discrete modules in sequence: preflight → download → transcribe → understand (Gemini) → frames → avt assembly → cleanup. Each module is a standalone script with a clear interface. Gemini 2.5 Flash provides native video understanding; frames are extracted at Gemini-identified timestamps via ffmpeg.

**Tech Stack:** Python 3.11+, yt-dlp (video download), ffmpeg/ffprobe (frame/audio extraction), Gemini 2.5 Flash (video understanding), Whisper via Groq/OpenAI (transcript fallback), python-dotenv (config), httpx (HTTP).

---

## File Structure

```
video-analyzer/
├── CLAUDE.md                          (exists)
├── requirements.txt                   (create — Python deps)
├── docs/
│   ├── avt-spec.md                    (exists)
│   ├── PRD.md                         (exists)
│   ├── scratchpad.md                  (exists)
│   └── specs/
│       └── 2026-05-16-video-analyzer-design.md (exists)
├── scripts/
│   ├── preflight.py                   (create — dependency checker)
│   ├── download.py                    (create — yt-dlp wrapper)
│   ├── transcribe.py                  (create — caption extraction + VTT parsing)
│   ├── whisper.py                     (create — Whisper API clients)
│   ├── understand.py                  (create — Gemini video understanding)
│   ├── frames.py                      (create — ffmpeg frame extraction)
│   ├── avt.py                         (create — .avt writer + parser)
│   ├── analyze.py                     (create — orchestrator / entry point)
│   └── prompts/
│       └── understand.txt             (create — Gemini prompt template)
├── tests/
│   ├── test_preflight.py              (create)
│   ├── test_download.py               (create)
│   ├── test_transcribe.py             (create)
│   ├── test_whisper.py                (create)
│   ├── test_understand.py             (create)
│   ├── test_frames.py                 (create)
│   ├── test_avt.py                    (create)
│   ├── test_analyze.py                (create)
│   └── fixtures/
│       ├── sample.vtt                 (create — test VTT file)
│       ├── sample.avt                 (create — test .avt file)
│       └── gemini_response.json       (create — mock Gemini output)
├── commands/
│   └── analyze.md                     (create — Claude Code command)
├── SKILL.md                           (create — skill definition)
├── README.md                          (create — public repo readme)
├── activity.md                        (exists)
├── LICENSE                            (exists)
└── .gitignore                         (exists)
```

---

## Task 1: Requirements and Test Infrastructure

**Files:**
- Create: `requirements.txt`
- Create: `tests/__init__.py`
- Create: `tests/fixtures/sample.vtt`
- Create: `tests/fixtures/gemini_response.json`
- Create: `tests/fixtures/sample.avt`

- [ ] **Step 1: Create requirements.txt**

```
google-genai>=1.0.0
httpx>=0.27.0
python-dotenv>=1.0.0
```

- [ ] **Step 2: Create test fixtures directory and sample VTT**

```
WEBVTT

00:00:00.000 --> 00:00:04.200
What's up guys, today I want to show you something

00:00:04.200 --> 00:00:08.500
that completely changed how I use Claude Code.

00:00:08.500 --> 00:00:15.000
So the first thing you need to do is install this package.
```

- [ ] **Step 3: Create sample Gemini response fixture**

```json
[
  {
    "start": "00:00",
    "end": "00:04",
    "visual": "Man sitting at desk, ring light behind. Dark room, low-budget setup.",
    "scene": "intro"
  },
  {
    "start": "00:04",
    "end": "00:15",
    "visual": "Screen recording of VS Code. Claude Code terminal visible in bottom panel.",
    "scene": "screen-recording"
  },
  {
    "start": "00:15",
    "end": "00:32",
    "visual": "Same screen recording. Terminal output scrolling rapidly.",
    "scene": "demo"
  }
]
```

- [ ] **Step 4: Create sample .avt fixture**

```
AGENTIC-VT 1.0

[metadata]
title: Test Video
channel: Test Channel
duration: 00:32
source: https://youtube.com/watch?v=test123
analyzed: 2026-05-16 14:30:00
model: gemini-2.5-flash
frames_extracted: 3
transcript_source: captions

---

[00:00 - 00:04] [scene:intro]
VISUAL: Man sitting at desk, ring light behind. Dark room, low-budget setup.
AUDIO: 'What\'s up guys, today I want to show you something that completely changed how I use Claude Code.'
FRAME: frames/frame-001.jpg

[00:04 - 00:15] [scene:screen-recording]
VISUAL: Screen recording of VS Code. Claude Code terminal visible in bottom panel.
AUDIO: 'So the first thing you need to do is install this package. Let me walk you through it step by step.'
FRAME: frames/frame-002.jpg

[00:15 - 00:32] [scene:demo]
VISUAL: Same screen recording. Terminal output scrolling rapidly.
AUDIO: 'And now you can see it\'s actually working.'
FRAME: frames/frame-003.jpg
```

- [ ] **Step 5: Create tests/__init__.py (empty)**

- [ ] **Step 6: Commit**

```bash
git add requirements.txt tests/
git commit -m "feat: add requirements.txt and test fixtures"
```

---

## Task 2: preflight.py — Dependency Checker

**Files:**
- Create: `scripts/preflight.py`
- Create: `tests/test_preflight.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_preflight.py
import subprocess
import sys
import os

def test_check_binary_found(monkeypatch):
    """check_binary returns True for a binary that exists."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
    from preflight import check_binary
    # 'python3' should always exist in test env
    assert check_binary('python3') is True

def test_check_binary_not_found(monkeypatch):
    """check_binary returns False for a binary that doesn't exist."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
    from preflight import check_binary
    assert check_binary('nonexistent_binary_xyz') is False

def test_check_api_key_present(monkeypatch, tmp_path):
    """check_api_keys finds keys in env file."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
    from preflight import check_api_keys
    env_file = tmp_path / ".env"
    env_file.write_text("GOOGLE_API_KEY=test123\n")
    result = check_api_keys(str(env_file))
    assert result['GOOGLE_API_KEY'] is True

def test_check_api_key_missing(tmp_path):
    """check_api_keys reports missing keys."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
    from preflight import check_api_keys
    env_file = tmp_path / ".env"
    env_file.write_text("GROQ_API_KEY=test\n")
    result = check_api_keys(str(env_file))
    assert result['GOOGLE_API_KEY'] is False

def test_preflight_check_returns_status():
    """preflight_check returns a dict with binaries and keys status."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
    from preflight import preflight_check
    # Use a non-existent env path so keys fail
    result = preflight_check(env_path='/tmp/nonexistent/.env')
    assert 'binaries' in result
    assert 'keys' in result
    assert 'ready' in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/franciscojosejimeneznillardkam/Documents/Frank\ DOCS/Frank\ Projects/video_understanding && python3 -m pytest tests/test_preflight.py -v`
Expected: FAIL — ModuleNotFoundError (preflight doesn't exist yet)

- [ ] **Step 3: Write preflight.py implementation**

```python
#!/usr/bin/env python3
"""Dependency checker for video-analyzer."""

import os
import shutil
import subprocess
import sys

CONFIG_DIR = os.path.expanduser("~/.config/video-analyzer")
ENV_FILE = os.path.join(CONFIG_DIR, ".env")

REQUIRED_BINARIES = ['ffmpeg', 'ffprobe', 'yt-dlp']
REQUIRED_KEYS = ['GOOGLE_API_KEY']
OPTIONAL_KEYS = ['GROQ_API_KEY', 'OPENAI_API_KEY']


def check_binary(name: str) -> bool:
    """Check if a binary is available on PATH."""
    return shutil.which(name) is not None


def check_api_keys(env_path: str = ENV_FILE) -> dict:
    """Check which API keys are present in the env file."""
    keys_found = {}
    all_keys = REQUIRED_KEYS + OPTIONAL_KEYS

    for key in all_keys:
        keys_found[key] = False

    if not os.path.exists(env_path):
        return keys_found

    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip()
                if k in all_keys and v:
                    keys_found[k] = True

    return keys_found


def preflight_check(env_path: str = ENV_FILE) -> dict:
    """Run all preflight checks. Returns status dict."""
    binaries = {name: check_binary(name) for name in REQUIRED_BINARIES}
    keys = check_api_keys(env_path)

    missing_binaries = [k for k, v in binaries.items() if not v]
    missing_required_keys = [k for k in REQUIRED_KEYS if not keys.get(k)]

    ready = len(missing_binaries) == 0 and len(missing_required_keys) == 0

    return {
        'binaries': binaries,
        'keys': keys,
        'missing_binaries': missing_binaries,
        'missing_required_keys': missing_required_keys,
        'ready': ready,
    }


def scaffold_env():
    """Create config dir and .env template if they don't exist."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'w') as f:
            f.write("# video-analyzer configuration\n")
            f.write("# Required:\n")
            f.write("GOOGLE_API_KEY=\n")
            f.write("\n# Optional (Whisper transcription):\n")
            f.write("GROQ_API_KEY=\n")
            f.write("OPENAI_API_KEY=\n")
        os.chmod(ENV_FILE, 0o600)
        print(f"Created config: {ENV_FILE}", file=sys.stderr)


def install_missing(binaries: list):
    """Attempt to install missing binaries via brew (macOS only)."""
    if sys.platform != 'darwin':
        print("Auto-install only supported on macOS. Install manually:", file=sys.stderr)
        for b in binaries:
            print(f"  - {b}", file=sys.stderr)
        return False

    if not check_binary('brew'):
        print("Homebrew not found. Install from https://brew.sh", file=sys.stderr)
        return False

    for binary in binaries:
        pkg = 'ffmpeg' if binary in ('ffmpeg', 'ffprobe') else binary
        print(f"Installing {pkg} via brew...", file=sys.stderr)
        result = subprocess.run(['brew', 'install', pkg], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to install {pkg}: {result.stderr}", file=sys.stderr)
            return False

    return True


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="video-analyzer preflight check")
    parser.add_argument('--check', action='store_true', help="Check only, don't install")
    args = parser.parse_args()

    status = preflight_check()

    # Report binaries
    for name, found in status['binaries'].items():
        icon = "OK" if found else "MISSING"
        print(f"  [{icon}] {name}", file=sys.stderr)

    # Report keys
    for key, found in status['keys'].items():
        required = key in REQUIRED_KEYS
        label = "required" if required else "optional"
        icon = "OK" if found else "MISSING"
        print(f"  [{icon}] {key} ({label})", file=sys.stderr)

    if status['ready']:
        print("\nAll checks passed. Ready to analyze.", file=sys.stderr)
        sys.exit(0)

    if args.check:
        # Check-only mode: report and exit
        has_bin = bool(status['missing_binaries'])
        has_key = bool(status['missing_required_keys'])
        if has_bin and has_key:
            sys.exit(4)
        if has_bin:
            sys.exit(2)
        if has_key:
            sys.exit(3)

    # Attempt fixes
    if status['missing_binaries']:
        install_missing(status['missing_binaries'])

    if status['missing_required_keys']:
        scaffold_env()
        print(f"\nAdd your API keys to: {ENV_FILE}", file=sys.stderr)
        sys.exit(3)

    # Re-check after install
    recheck = preflight_check()
    if recheck['ready']:
        print("\nAll checks passed. Ready to analyze.", file=sys.stderr)
        sys.exit(0)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/franciscojosejimeneznillardkam/Documents/Frank\ DOCS/Frank\ Projects/video_understanding && python3 -m pytest tests/test_preflight.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/preflight.py tests/test_preflight.py
git commit -m "feat: add preflight.py dependency checker"
```

---

## Task 3: download.py — Video Acquisition

**Files:**
- Create: `scripts/download.py`
- Create: `tests/test_download.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_download.py
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def test_is_url_true():
    from download import is_url
    assert is_url("https://youtube.com/watch?v=abc123") is True
    assert is_url("http://example.com/video.mp4") is True


def test_is_url_false():
    from download import is_url
    assert is_url("/path/to/video.mp4") is False
    assert is_url("relative/path.mp4") is False


def test_get_slug_from_title():
    from download import get_slug
    assert get_slug("How I Built X With Claude Code") == "how-i-built-x-with-claude-code"
    assert get_slug("Test! @Video #123") == "test-video-123"


def test_local_file_passthrough(tmp_path):
    from download import download_video
    # Create a fake video file
    video = tmp_path / "test.mp4"
    video.write_bytes(b'\x00' * 100)

    result = download_video(str(video), str(tmp_path))
    assert result['video_path'] == str(video)
    assert result['is_local'] is True


def test_download_rejects_missing_file():
    from download import download_video
    import pytest
    with pytest.raises(FileNotFoundError):
        download_video("/nonexistent/video.mp4", "/tmp")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_download.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Write download.py implementation**

```python
#!/usr/bin/env python3
"""Video download module — wraps yt-dlp for URL sources, passes through local files."""

import json
import os
import re
import subprocess
import sys


def is_url(source: str) -> bool:
    """Check if source is a URL (vs local file path)."""
    return source.startswith('http://') or source.startswith('https://')


def get_slug(title: str) -> str:
    """Convert a title to a URL-safe slug."""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug.strip())
    slug = re.sub(r'-+', '-', slug)
    return slug


def download_video(source: str, cache_dir: str) -> dict:
    """
    Download video from URL or validate local file.

    Returns:
        {
            'video_path': str,        # path to video file
            'subtitle_path': str|None, # path to .vtt subtitle if found
            'title': str,
            'uploader': str,
            'duration': int,          # seconds
            'slug': str,
            'is_local': bool,
        }
    """
    if not is_url(source):
        # Local file — validate and pass through
        if not os.path.exists(source):
            raise FileNotFoundError(f"Video file not found: {source}")

        filename = os.path.basename(source)
        title = os.path.splitext(filename)[0]
        return {
            'video_path': source,
            'subtitle_path': None,
            'title': title,
            'uploader': 'local',
            'duration': _get_duration(source),
            'slug': get_slug(title),
            'is_local': True,
        }

    # URL — download via yt-dlp
    os.makedirs(cache_dir, exist_ok=True)

    # First get metadata
    meta_cmd = [
        'yt-dlp', '--dump-json', '--no-download', source
    ]
    print(f"Fetching metadata...", file=sys.stderr)
    meta_result = subprocess.run(meta_cmd, capture_output=True, text=True)

    if meta_result.returncode != 0:
        error = meta_result.stderr.strip()
        if 'private' in error.lower() or 'sign in' in error.lower():
            raise PermissionError(f"Video requires authentication: {error}")
        if 'age' in error.lower():
            raise PermissionError(f"Age-restricted video: {error}")
        raise RuntimeError(f"yt-dlp metadata failed: {error}")

    meta = json.loads(meta_result.stdout)
    title = meta.get('title', 'untitled')
    uploader = meta.get('uploader', 'unknown')
    duration = meta.get('duration', 0)
    slug = get_slug(title)

    # Check file size estimate (reject > 2GB)
    filesize = meta.get('filesize') or meta.get('filesize_approx') or 0
    if filesize > 2 * 1024 * 1024 * 1024:
        raise ValueError(f"Video too large ({filesize / 1e9:.1f} GB). Max 2 GB for Gemini upload.")

    # Download video + subtitles
    output_template = os.path.join(cache_dir, f"{slug}.%(ext)s")
    dl_cmd = [
        'yt-dlp',
        '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '--write-subs', '--write-auto-subs',
        '--sub-langs', 'en.*,en',
        '--sub-format', 'vtt',
        '--no-playlist',
        '-o', output_template,
        source,
    ]
    print(f"Downloading: {title}...", file=sys.stderr)
    dl_result = subprocess.run(dl_cmd, capture_output=True, text=True)

    if dl_result.returncode != 0:
        raise RuntimeError(f"yt-dlp download failed: {dl_result.stderr.strip()}")

    # Find downloaded files
    video_path = None
    subtitle_path = None
    for f in os.listdir(cache_dir):
        full = os.path.join(cache_dir, f)
        if f.endswith('.vtt') and subtitle_path is None:
            subtitle_path = full
        elif not f.endswith('.vtt') and not f.endswith('.json'):
            video_path = full

    if not video_path:
        raise RuntimeError("Download completed but video file not found in cache dir")

    return {
        'video_path': video_path,
        'subtitle_path': subtitle_path,
        'title': title,
        'uploader': uploader,
        'duration': duration,
        'slug': slug,
        'is_local': False,
    }


def _get_duration(video_path: str) -> int:
    """Get video duration in seconds via ffprobe."""
    cmd = [
        'ffprobe', '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return 0
    try:
        data = json.loads(result.stdout)
        return int(float(data['format']['duration']))
    except (KeyError, ValueError, json.JSONDecodeError):
        return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_download.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/download.py tests/test_download.py
git commit -m "feat: add download.py video acquisition module"
```

---

## Task 4: transcribe.py — Caption Extraction and VTT Parsing

**Files:**
- Create: `scripts/transcribe.py`
- Create: `tests/test_transcribe.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_transcribe.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')


def test_parse_vtt_basic():
    from transcribe import parse_vtt
    vtt_path = os.path.join(FIXTURES, 'sample.vtt')
    segments = parse_vtt(vtt_path)
    assert len(segments) == 3
    assert segments[0]['start'] == '00:00'
    assert segments[0]['text'] == "What's up guys, today I want to show you something"


def test_parse_vtt_strips_html_tags():
    from transcribe import parse_vtt_content
    content = """WEBVTT

00:00:00.000 --> 00:00:03.000
<c>Hello</c> <b>world</b>
"""
    segments = parse_vtt_content(content)
    assert segments[0]['text'] == "Hello world"


def test_parse_vtt_deduplicates_rolling_captions():
    from transcribe import parse_vtt_content
    content = """WEBVTT

00:00:00.000 --> 00:00:02.000
Hello world

00:00:02.000 --> 00:00:04.000
Hello world

00:00:04.000 --> 00:00:06.000
Something new
"""
    segments = parse_vtt_content(content)
    # Adjacent duplicates should be merged
    assert len(segments) == 2
    assert segments[0]['text'] == "Hello world"
    assert segments[1]['text'] == "Something new"


def test_format_timestamp_seconds():
    from transcribe import format_timestamp
    assert format_timestamp(0) == "00:00"
    assert format_timestamp(65) == "01:05"
    assert format_timestamp(3661) == "1:01:01"


def test_get_transcript_from_vtt(tmp_path):
    from transcribe import get_transcript
    import shutil
    vtt_src = os.path.join(FIXTURES, 'sample.vtt')
    vtt_dst = tmp_path / "subs.vtt"
    shutil.copy(vtt_src, vtt_dst)

    result = get_transcript(subtitle_path=str(vtt_dst))
    assert result['source'] == 'captions'
    assert len(result['segments']) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_transcribe.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Write transcribe.py implementation**

```python
#!/usr/bin/env python3
"""Transcript extraction — VTT parsing with HTML cleanup and deduplication."""

import os
import re
import sys


def format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS or H:MM:SS format."""
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _parse_vtt_timestamp(ts: str) -> float:
    """Parse VTT timestamp (HH:MM:SS.mmm) to seconds."""
    parts = ts.strip().split(':')
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return 0.0


def _strip_html(text: str) -> str:
    """Remove HTML/VTT tags from text."""
    return re.sub(r'<[^>]+>', '', text)


def parse_vtt_content(content: str) -> list:
    """Parse VTT content string into segments with deduplication."""
    lines = content.strip().split('\n')
    segments = []
    current_start = None
    current_end = None
    current_text = []

    timestamp_re = re.compile(r'(\d{1,2}:\d{2}(?::\d{2})?\.\d{3})\s*-->\s*(\d{1,2}:\d{2}(?::\d{2})?\.\d{3})')

    for line in lines:
        line = line.strip()

        # Skip WEBVTT header and empty lines
        if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
            continue

        # Skip numeric cue identifiers
        if line.isdigit():
            continue

        match = timestamp_re.match(line)
        if match:
            # Save previous segment
            if current_text:
                text = _strip_html(' '.join(current_text)).strip()
                text = re.sub(r'\s+', ' ', text)
                if text:
                    segments.append({
                        'start': format_timestamp(current_start),
                        'end': format_timestamp(current_end),
                        'start_seconds': current_start,
                        'end_seconds': current_end,
                        'text': text,
                    })

            current_start = _parse_vtt_timestamp(match.group(1))
            current_end = _parse_vtt_timestamp(match.group(2))
            current_text = []
        elif line and current_start is not None:
            current_text.append(line)

    # Save last segment
    if current_text:
        text = _strip_html(' '.join(current_text)).strip()
        text = re.sub(r'\s+', ' ', text)
        if text:
            segments.append({
                'start': format_timestamp(current_start),
                'end': format_timestamp(current_end),
                'start_seconds': current_start,
                'end_seconds': current_end,
                'text': text,
            })

    # Deduplicate adjacent identical captions (YouTube rolling captions)
    deduped = []
    for seg in segments:
        if deduped and deduped[-1]['text'] == seg['text']:
            # Extend the end time of the previous segment
            deduped[-1]['end'] = seg['end']
            deduped[-1]['end_seconds'] = seg['end_seconds']
        else:
            deduped.append(seg)

    return deduped


def parse_vtt(vtt_path: str) -> list:
    """Parse a VTT file into segments."""
    with open(vtt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return parse_vtt_content(content)


def get_transcript(subtitle_path: str = None, video_path: str = None,
                   whisper_backend: str = 'auto', no_whisper: bool = False) -> dict:
    """
    Get transcript for a video.

    Priority:
    1. Native captions (subtitle_path)
    2. Whisper fallback (if enabled)
    3. Empty segments (no speech)

    Returns:
        {'segments': [...], 'source': 'captions'|'whisper-groq'|'whisper-openai'|'none'}
    """
    # Try native captions first
    if subtitle_path and os.path.exists(subtitle_path):
        segments = parse_vtt(subtitle_path)
        if segments:
            print(f"Using native captions ({len(segments)} segments)", file=sys.stderr)
            return {'segments': segments, 'source': 'captions'}

    # Try Whisper fallback
    if not no_whisper and video_path:
        try:
            from whisper import transcribe_with_whisper
            result = transcribe_with_whisper(video_path, backend=whisper_backend)
            if result and result['segments']:
                return result
        except ImportError:
            print("Whisper module not available", file=sys.stderr)
        except Exception as e:
            print(f"Whisper failed: {e}", file=sys.stderr)

    # No transcript available
    return {'segments': [], 'source': 'none'}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_transcribe.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/transcribe.py tests/test_transcribe.py
git commit -m "feat: add transcribe.py VTT parsing with dedup"
```

---

## Task 5: whisper.py — Whisper API Clients

**Files:**
- Create: `scripts/whisper.py`
- Create: `tests/test_whisper.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_whisper.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def test_extract_audio_command():
    """Verify the ffmpeg command is constructed correctly."""
    from whisper import _build_audio_extract_cmd
    cmd = _build_audio_extract_cmd("/path/to/video.mp4", "/tmp/audio.wav")
    assert 'ffmpeg' in cmd[0]
    assert '-ar' in cmd
    assert '16000' in cmd
    assert '/tmp/audio.wav' in cmd


def test_select_backend_groq(monkeypatch):
    """Auto-selects groq when GROQ_API_KEY is available."""
    from whisper import select_backend
    keys = {'GROQ_API_KEY': True, 'OPENAI_API_KEY': False}
    assert select_backend('auto', keys) == 'groq'


def test_select_backend_openai_fallback(monkeypatch):
    """Falls back to openai when groq unavailable."""
    from whisper import select_backend
    keys = {'GROQ_API_KEY': False, 'OPENAI_API_KEY': True}
    assert select_backend('auto', keys) == 'openai'


def test_select_backend_none():
    """Returns None when no keys available."""
    from whisper import select_backend
    keys = {'GROQ_API_KEY': False, 'OPENAI_API_KEY': False}
    assert select_backend('auto', keys) is None


def test_select_backend_forced():
    """Respects forced backend selection."""
    from whisper import select_backend
    keys = {'GROQ_API_KEY': True, 'OPENAI_API_KEY': True}
    assert select_backend('openai', keys) == 'openai'
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_whisper.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Write whisper.py implementation**

```python
#!/usr/bin/env python3
"""Whisper API clients for audio transcription (Groq and OpenAI)."""

import json
import os
import subprocess
import sys
import tempfile

import httpx


def _build_audio_extract_cmd(video_path: str, audio_path: str) -> list:
    """Build ffmpeg command to extract mono 16kHz audio."""
    return [
        'ffmpeg', '-y', '-i', video_path,
        '-vn', '-ac', '1', '-ar', '16000',
        '-f', 'wav', audio_path,
    ]


def select_backend(preference: str, keys: dict) -> str | None:
    """Select whisper backend based on preference and available keys."""
    if preference == 'groq':
        return 'groq' if keys.get('GROQ_API_KEY') else None
    if preference == 'openai':
        return 'openai' if keys.get('OPENAI_API_KEY') else None

    # Auto: prefer groq, fallback to openai
    if keys.get('GROQ_API_KEY'):
        return 'groq'
    if keys.get('OPENAI_API_KEY'):
        return 'openai'
    return None


def _extract_audio(video_path: str, cache_dir: str) -> str:
    """Extract audio from video to WAV file."""
    audio_path = os.path.join(cache_dir, 'audio.wav')
    cmd = _build_audio_extract_cmd(video_path, audio_path)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Audio extraction failed: {result.stderr}")
    return audio_path


def _transcribe_groq(audio_path: str, api_key: str) -> list:
    """Transcribe audio using Groq Whisper API."""
    with open(audio_path, 'rb') as f:
        response = httpx.post(
            'https://api.groq.com/openai/v1/audio/transcriptions',
            headers={'Authorization': f'Bearer {api_key}'},
            files={'file': ('audio.wav', f, 'audio/wav')},
            data={
                'model': 'whisper-large-v3',
                'response_format': 'verbose_json',
                'timestamp_granularities[]': 'segment',
            },
            timeout=300,
        )

    if response.status_code != 200:
        raise RuntimeError(f"Groq Whisper API error: {response.status_code} {response.text}")

    data = response.json()
    segments = []
    for seg in data.get('segments', []):
        from transcribe import format_timestamp
        segments.append({
            'start': format_timestamp(seg['start']),
            'end': format_timestamp(seg['end']),
            'start_seconds': seg['start'],
            'end_seconds': seg['end'],
            'text': seg['text'].strip(),
        })
    return segments


def _transcribe_openai(audio_path: str, api_key: str) -> list:
    """Transcribe audio using OpenAI Whisper API."""
    with open(audio_path, 'rb') as f:
        response = httpx.post(
            'https://api.openai.com/v1/audio/transcriptions',
            headers={'Authorization': f'Bearer {api_key}'},
            files={'file': ('audio.wav', f, 'audio/wav')},
            data={
                'model': 'whisper-1',
                'response_format': 'verbose_json',
                'timestamp_granularities[]': 'segment',
            },
            timeout=300,
        )

    if response.status_code != 200:
        raise RuntimeError(f"OpenAI Whisper API error: {response.status_code} {response.text}")

    data = response.json()
    segments = []
    for seg in data.get('segments', []):
        from transcribe import format_timestamp
        segments.append({
            'start': format_timestamp(seg['start']),
            'end': format_timestamp(seg['end']),
            'start_seconds': seg['start'],
            'end_seconds': seg['end'],
            'text': seg['text'].strip(),
        })
    return segments


def transcribe_with_whisper(video_path: str, backend: str = 'auto',
                            env_path: str = None) -> dict:
    """
    Transcribe video using Whisper API.

    Returns: {'segments': [...], 'source': 'whisper-groq'|'whisper-openai'}
    """
    from preflight import check_api_keys, ENV_FILE
    env = env_path or ENV_FILE
    keys = check_api_keys(env)

    selected = select_backend(backend, keys)
    if not selected:
        raise RuntimeError("No Whisper API key available (need GROQ_API_KEY or OPENAI_API_KEY)")

    # Extract audio
    cache_dir = tempfile.mkdtemp(prefix='whisper-')
    try:
        print(f"Extracting audio for Whisper ({selected})...", file=sys.stderr)
        audio_path = _extract_audio(video_path, cache_dir)

        # Check audio size (skip if tiny = likely silence)
        audio_size = os.path.getsize(audio_path)
        if audio_size < 10000:  # < 10KB likely means no audio
            return {'segments': [], 'source': 'none'}

        if selected == 'groq':
            api_key = _load_key('GROQ_API_KEY', env)
            segments = _transcribe_groq(audio_path, api_key)
            source = 'whisper-groq'
        else:
            api_key = _load_key('OPENAI_API_KEY', env)
            segments = _transcribe_openai(audio_path, api_key)
            source = 'whisper-openai'

        print(f"Whisper returned {len(segments)} segments", file=sys.stderr)
        return {'segments': segments, 'source': source}
    finally:
        # Cleanup temp audio
        import shutil
        shutil.rmtree(cache_dir, ignore_errors=True)


def _load_key(key_name: str, env_path: str) -> str:
    """Load a specific API key from env file."""
    if not os.path.exists(env_path):
        raise RuntimeError(f"Config file not found: {env_path}")
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith(f'{key_name}='):
                return line.split('=', 1)[1].strip()
    raise RuntimeError(f"{key_name} not found in {env_path}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_whisper.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/whisper.py tests/test_whisper.py
git commit -m "feat: add whisper.py API clients (Groq + OpenAI)"
```

---

## Task 6: understand.py — Gemini Video Understanding

**Files:**
- Create: `scripts/understand.py`
- Create: `scripts/prompts/understand.txt`
- Create: `tests/test_understand.py`

- [ ] **Step 1: Create the Gemini prompt template**

```
Analyze this video and identify all key visual moments. For each distinct visual segment, provide:
- start: timestamp when this segment begins (MM:SS format)
- end: timestamp when this segment ends (MM:SS format)
- visual: 1-2 sentence description of what is shown on screen. Focus on: environment/setup, screen content, people visible, text on screen, production quality indicators.
- scene: one tag from this list: intro, outro, hook, cta, sponsor, talking-head, screen-recording, demo, tutorial, slide, diagram, whiteboard, code, b-roll, montage, transition, interview, reaction, commentary, other

Return ONLY the JSON array. Aim for segments of 3-30 seconds each. Capture every meaningful visual change.
```

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_understand.py
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')


def test_validate_scene_tags():
    from understand import VALID_SCENE_TAGS, validate_segments
    segments = [
        {"start": "00:00", "end": "00:10", "visual": "test", "scene": "intro"},
        {"start": "00:10", "end": "00:20", "visual": "test", "scene": "invalid-tag"},
    ]
    validated = validate_segments(segments)
    assert validated[0]['scene'] == 'intro'
    assert validated[1]['scene'] == 'other'  # invalid replaced with 'other'


def test_parse_gemini_response():
    from understand import parse_gemini_response
    fixture_path = os.path.join(FIXTURES, 'gemini_response.json')
    with open(fixture_path, 'r') as f:
        raw = f.read()
    segments = parse_gemini_response(raw)
    assert len(segments) == 3
    assert segments[0]['scene'] == 'intro'
    assert segments[0]['start'] == '00:00'


def test_get_prompt():
    from understand import get_prompt
    prompt = get_prompt()
    assert 'visual' in prompt
    assert 'scene' in prompt
    assert 'JSON' in prompt


def test_valid_scene_tags_list():
    from understand import VALID_SCENE_TAGS
    assert 'intro' in VALID_SCENE_TAGS
    assert 'talking-head' in VALID_SCENE_TAGS
    assert 'other' in VALID_SCENE_TAGS
    assert len(VALID_SCENE_TAGS) == 20
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_understand.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 4: Write understand.py implementation**

```python
#!/usr/bin/env python3
"""Gemini video understanding — uploads video and gets structured visual analysis."""

import json
import os
import sys
import time

VALID_SCENE_TAGS = [
    'intro', 'outro', 'hook', 'cta', 'sponsor',
    'talking-head', 'screen-recording', 'demo', 'tutorial',
    'slide', 'diagram', 'whiteboard', 'code',
    'b-roll', 'montage', 'transition',
    'interview', 'reaction', 'commentary',
    'other',
]

RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "start": {"type": "string"},
            "end": {"type": "string"},
            "visual": {"type": "string"},
            "scene": {"type": "string", "enum": VALID_SCENE_TAGS},
        },
        "required": ["start", "end", "visual", "scene"],
    },
}

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), 'prompts')
POLL_INTERVAL = 5  # seconds
POLL_TIMEOUT = 300  # 5 minutes


def get_prompt() -> str:
    """Load the Gemini prompt template."""
    prompt_path = os.path.join(PROMPTS_DIR, 'understand.txt')
    with open(prompt_path, 'r') as f:
        return f.read().strip()


def validate_segments(segments: list) -> list:
    """Validate and fix scene tags in segments."""
    for seg in segments:
        if seg.get('scene') not in VALID_SCENE_TAGS:
            seg['scene'] = 'other'
    return segments


def parse_gemini_response(raw_text: str) -> list:
    """Parse Gemini's JSON response into validated segments."""
    # Handle both raw JSON and markdown-wrapped JSON
    text = raw_text.strip()
    if text.startswith('```'):
        # Strip markdown code fences
        lines = text.split('\n')
        lines = [l for l in lines if not l.strip().startswith('```')]
        text = '\n'.join(lines)

    segments = json.loads(text)
    return validate_segments(segments)


def understand_video(video_path: str, api_key: str) -> list:
    """
    Upload video to Gemini and get structured visual analysis.

    Returns: list of segment dicts [{start, end, visual, scene}, ...]
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    # Upload video file
    file_size = os.path.getsize(video_path)
    print(f"Uploading video ({file_size / 1e6:.1f} MB) to Gemini...", file=sys.stderr)

    uploaded_file = client.files.upload(file=video_path)
    print(f"Upload complete. Processing...", file=sys.stderr)

    try:
        # Poll until ACTIVE
        elapsed = 0
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL
            if elapsed >= POLL_TIMEOUT:
                raise TimeoutError(f"Gemini file processing timed out after {POLL_TIMEOUT}s")
            uploaded_file = client.files.get(name=uploaded_file.name)

        if uploaded_file.state.name != "ACTIVE":
            raise RuntimeError(f"Gemini file in unexpected state: {uploaded_file.state.name}")

        print("Video ready. Analyzing...", file=sys.stderr)

        # Generate content with structured output
        prompt = get_prompt()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[uploaded_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
            ),
        )

        segments = parse_gemini_response(response.text)
        print(f"Gemini identified {len(segments)} visual segments", file=sys.stderr)
        return segments

    finally:
        # Always delete uploaded file
        try:
            client.files.delete(name=uploaded_file.name)
            print("Cleaned up Gemini uploaded file", file=sys.stderr)
        except Exception as e:
            print(f"Warning: failed to delete Gemini file: {e}", file=sys.stderr)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_understand.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/understand.py scripts/prompts/understand.txt tests/test_understand.py
git commit -m "feat: add understand.py Gemini video analysis"
```

---

## Task 7: frames.py — Frame Extraction

**Files:**
- Create: `scripts/frames.py`
- Create: `tests/test_frames.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_frames.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def test_timestamp_to_seconds():
    from frames import timestamp_to_seconds
    assert timestamp_to_seconds("00:00") == 0
    assert timestamp_to_seconds("01:30") == 90
    assert timestamp_to_seconds("1:00:00") == 3600
    assert timestamp_to_seconds("00:05") == 5


def test_build_ffmpeg_command():
    from frames import _build_frame_cmd
    cmd = _build_frame_cmd("/video.mp4", 30.0, "/out/frame-001.jpg", 512)
    assert 'ffmpeg' in cmd[0]
    assert '-ss' in cmd
    assert '30.0' in cmd or '30' in cmd
    assert '/out/frame-001.jpg' in cmd


def test_select_timestamps_under_max():
    from frames import select_timestamps
    timestamps = [0, 10, 20, 30, 40]
    result = select_timestamps(timestamps, max_frames=80)
    assert result == timestamps  # all fit


def test_select_timestamps_over_max():
    from frames import select_timestamps
    timestamps = list(range(100))  # 0-99
    result = select_timestamps(timestamps, max_frames=10)
    assert len(result) == 10
    # Should be evenly spaced
    assert result[0] == 0
    assert result[-1] == 99


def test_get_frame_filename():
    from frames import get_frame_filename
    assert get_frame_filename(0) == "frame-001.jpg"
    assert get_frame_filename(9) == "frame-010.jpg"
    assert get_frame_filename(99) == "frame-100.jpg"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_frames.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Write frames.py implementation**

```python
#!/usr/bin/env python3
"""Frame extraction — extract JPEG frames at Gemini-identified timestamps."""

import os
import subprocess
import sys


def timestamp_to_seconds(ts: str) -> float:
    """Convert MM:SS or H:MM:SS timestamp to seconds."""
    parts = ts.split(':')
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return 0.0


def get_frame_filename(index: int) -> str:
    """Generate frame filename from index (0-based)."""
    return f"frame-{index + 1:03d}.jpg"


def select_timestamps(timestamps: list, max_frames: int = 80) -> list:
    """Select evenly-spaced subset if over max_frames limit."""
    if len(timestamps) <= max_frames:
        return timestamps

    # Evenly space, always include first and last
    step = (len(timestamps) - 1) / (max_frames - 1)
    indices = [round(i * step) for i in range(max_frames)]
    return [timestamps[i] for i in indices]


def _build_frame_cmd(video_path: str, seconds: float, output_path: str, width: int) -> list:
    """Build ffmpeg command to extract a single frame."""
    return [
        'ffmpeg', '-y',
        '-ss', str(seconds),
        '-i', video_path,
        '-vframes', '1',
        '-vf', f'scale={width}:-1',
        '-q:v', '2',
        output_path,
    ]


def extract_frames(video_path: str, segments: list, output_dir: str,
                   max_frames: int = 80, width: int = 512) -> list:
    """
    Extract JPEG frames at segment start timestamps.

    Args:
        video_path: Path to video file
        segments: List of dicts with 'start' key (from understand.py)
        output_dir: Directory to write frames/ into
        max_frames: Maximum number of frames to extract
        width: Frame width in pixels

    Returns:
        List of {'path': str, 'timestamp': str, 'seconds': float}
    """
    frames_dir = os.path.join(output_dir, 'frames')
    os.makedirs(frames_dir, exist_ok=True)

    # Get all start timestamps as seconds
    all_timestamps = []
    for seg in segments:
        seconds = timestamp_to_seconds(seg['start'])
        all_timestamps.append(seconds)

    # Select subset if over limit
    selected = select_timestamps(all_timestamps, max_frames)

    results = []
    total = len(selected)
    for i, seconds in enumerate(selected):
        filename = get_frame_filename(i)
        output_path = os.path.join(frames_dir, filename)

        cmd = _build_frame_cmd(video_path, seconds, output_path, width)
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Warning: frame extraction failed at {seconds}s: {result.stderr}", file=sys.stderr)
            continue

        relative_path = os.path.join('frames', filename)
        results.append({
            'path': relative_path,
            'timestamp': _seconds_to_timestamp(seconds),
            'seconds': seconds,
        })

        if (i + 1) % 10 == 0 or i == total - 1:
            print(f"Extracted {i + 1}/{total} frames", file=sys.stderr)

    return results


def _seconds_to_timestamp(seconds: float) -> str:
    """Convert seconds back to MM:SS or H:MM:SS."""
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h > 0:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_frames.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/frames.py tests/test_frames.py
git commit -m "feat: add frames.py extraction at Gemini timestamps"
```

---

## Task 8: avt.py — Format Writer and Parser

**Files:**
- Create: `scripts/avt.py`
- Create: `tests/test_avt.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_avt.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')


def test_parse_avt_header():
    from avt import parse_avt
    fixture_path = os.path.join(FIXTURES, 'sample.avt')
    result = parse_avt(fixture_path)
    assert result['version'] == '1.0'
    assert result['metadata']['title'] == 'Test Video'
    assert result['metadata']['channel'] == 'Test Channel'
    assert result['metadata']['frames_extracted'] == 3


def test_parse_avt_segments():
    from avt import parse_avt
    fixture_path = os.path.join(FIXTURES, 'sample.avt')
    result = parse_avt(fixture_path)
    assert len(result['segments']) == 3
    seg = result['segments'][0]
    assert seg['start'] == '00:00'
    assert seg['end'] == '00:04'
    assert seg['scene'] == 'intro'
    assert 'ring light' in seg['visual']
    assert seg['frame'] == 'frames/frame-001.jpg'


def test_parse_avt_audio_with_escaped_quotes():
    from avt import parse_avt
    fixture_path = os.path.join(FIXTURES, 'sample.avt')
    result = parse_avt(fixture_path)
    seg = result['segments'][0]
    # Escaped quote should be unescaped in parsed output
    assert "What's up" in seg['audio']


def test_parse_avt_segment_without_frame():
    """Segments may omit the FRAME line."""
    from avt import parse_avt_content
    content = """AGENTIC-VT 1.0

[metadata]
title: Test
channel: Test
duration: 00:10
source: test
analyzed: 2026-01-01 00:00:00
model: test
frames_extracted: 0
transcript_source: none

---

[00:00 - 00:10] [scene:talking-head]
VISUAL: Person talking to camera.
AUDIO: 'Hello world'
"""
    result = parse_avt_content(content)
    assert result['segments'][0]['frame'] is None


def test_write_avt(tmp_path):
    from avt import write_avt, parse_avt

    metadata = {
        'title': 'Write Test',
        'channel': 'Test Channel',
        'duration': '00:30',
        'source': 'https://example.com/video',
        'analyzed': '2026-05-16 10:00:00',
        'model': 'gemini-2.5-flash',
        'frames_extracted': 2,
        'transcript_source': 'captions',
    }
    segments = [
        {
            'start': '00:00',
            'end': '00:15',
            'scene': 'intro',
            'visual': 'Person at desk with microphone.',
            'audio': "Hello, let's get started.",
            'frame': 'frames/frame-001.jpg',
        },
        {
            'start': '00:15',
            'end': '00:30',
            'scene': 'demo',
            'visual': 'Screen recording of terminal.',
            'audio': "Now I'll show you the demo.",
            'frame': 'frames/frame-002.jpg',
        },
    ]

    output_path = str(tmp_path / "test.avt")
    write_avt(metadata, segments, output_path)

    # Verify by parsing back
    result = parse_avt(output_path)
    assert result['version'] == '1.0'
    assert result['metadata']['title'] == 'Write Test'
    assert len(result['segments']) == 2
    assert result['segments'][0]['audio'] == "Hello, let's get started."


def test_write_avt_escapes_quotes(tmp_path):
    from avt import write_avt, parse_avt

    metadata = {
        'title': 'Quote Test',
        'channel': 'Test',
        'duration': '00:10',
        'source': 'test',
        'analyzed': '2026-01-01 00:00:00',
        'model': 'test',
        'frames_extracted': 0,
        'transcript_source': 'none',
    }
    segments = [
        {
            'start': '00:00',
            'end': '00:10',
            'scene': 'talking-head',
            'visual': 'Person talking.',
            'audio': "It's a test with single 'quotes' inside.",
            'frame': None,
        },
    ]

    output_path = str(tmp_path / "quotes.avt")
    write_avt(metadata, segments, output_path)

    result = parse_avt(output_path)
    assert result['segments'][0]['audio'] == "It's a test with single 'quotes' inside."
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_avt.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Write avt.py implementation**

```python
#!/usr/bin/env python3
"""AVT format writer and parser — Agentic Video Transcript."""

import os
import re
import sys

FORMAT_VERSION = "1.0"
FORMAT_HEADER = f"AGENTIC-VT {FORMAT_VERSION}"

# Regex patterns for parsing
RE_HEADER = re.compile(r'^AGENTIC-VT (\d+\.\d+)$')
RE_METADATA = re.compile(r'^(\w+):\s*(.+)$')
RE_SEPARATOR = re.compile(r'^---$')
RE_SEGMENT = re.compile(
    r'^\[(\d{1,2}:\d{2}(?::\d{2})?) - (\d{1,2}:\d{2}(?::\d{2})?)\] \[scene:([a-z0-9-]+)\]$'
)
RE_VISUAL = re.compile(r'^VISUAL:\s*(.+)$')
RE_AUDIO = re.compile(r"^AUDIO:\s*'(.*)'$")
RE_FRAME = re.compile(r'^FRAME:\s*(.+)$')

INT_METADATA_FIELDS = {'frames_extracted'}


def write_avt(metadata: dict, segments: list, output_path: str):
    """
    Write an .avt file.

    Args:
        metadata: dict with title, channel, duration, source, analyzed, model,
                  frames_extracted, transcript_source
        segments: list of dicts with start, end, scene, visual, audio, frame (or None)
        output_path: path to write the .avt file
    """
    lines = [FORMAT_HEADER, '', '[metadata]']

    # Write metadata
    field_order = ['title', 'channel', 'duration', 'source', 'analyzed',
                   'model', 'frames_extracted', 'transcript_source']
    for field in field_order:
        value = metadata.get(field, '')
        lines.append(f"{field}: {value}")

    lines.append('')
    lines.append('---')

    # Write segments
    for seg in segments:
        lines.append('')
        lines.append(f"[{seg['start']} - {seg['end']}] [scene:{seg['scene']}]")
        lines.append(f"VISUAL: {seg['visual']}")

        # Escape single quotes in audio
        audio = seg.get('audio', '')
        escaped_audio = audio.replace("'", "\\'")
        lines.append(f"AUDIO: '{escaped_audio}'")

        if seg.get('frame'):
            lines.append(f"FRAME: {seg['frame']}")

    lines.append('')  # trailing newline

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def parse_avt(file_path: str) -> dict:
    """Parse an .avt file into structured dict."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return parse_avt_content(content)


def parse_avt_content(content: str) -> dict:
    """Parse .avt content string into structured dict."""
    lines = content.split('\n')

    # Verify header
    if not lines or not RE_HEADER.match(lines[0].strip()):
        raise ValueError(f"Invalid .avt file: missing AGENTIC-VT header")

    version_match = RE_HEADER.match(lines[0].strip())
    version = version_match.group(1)

    if version != FORMAT_VERSION:
        raise ValueError(f"Unsupported .avt version: {version} (expected {FORMAT_VERSION})")

    # Parse metadata
    metadata = {}
    in_metadata = False
    separator_idx = None

    for i, line in enumerate(lines[1:], 1):
        line = line.strip()
        if line == '[metadata]':
            in_metadata = True
            continue
        if RE_SEPARATOR.match(line):
            separator_idx = i
            break
        if in_metadata:
            m = RE_METADATA.match(line)
            if m:
                key, value = m.group(1), m.group(2)
                if key in INT_METADATA_FIELDS:
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                metadata[key] = value

    if separator_idx is None:
        raise ValueError("Invalid .avt file: missing --- separator")

    # Parse segments
    segments = []
    current_segment = None

    for line in lines[separator_idx + 1:]:
        line_stripped = line.strip()

        if not line_stripped:
            if current_segment:
                segments.append(current_segment)
                current_segment = None
            continue

        seg_match = RE_SEGMENT.match(line_stripped)
        if seg_match:
            if current_segment:
                segments.append(current_segment)
            current_segment = {
                'start': seg_match.group(1),
                'end': seg_match.group(2),
                'scene': seg_match.group(3),
                'visual': '',
                'audio': '',
                'frame': None,
            }
            continue

        if current_segment:
            vis_match = RE_VISUAL.match(line_stripped)
            if vis_match:
                current_segment['visual'] = vis_match.group(1)
                continue

            aud_match = RE_AUDIO.match(line_stripped)
            if aud_match:
                # Unescape single quotes
                current_segment['audio'] = aud_match.group(1).replace("\\'", "'")
                continue

            frame_match = RE_FRAME.match(line_stripped)
            if frame_match:
                current_segment['frame'] = frame_match.group(1)
                continue

    # Don't forget last segment
    if current_segment:
        segments.append(current_segment)

    return {
        'version': version,
        'metadata': metadata,
        'segments': segments,
    }


def align_transcript_to_segments(transcript_segments: list, visual_segments: list) -> list:
    """
    Align transcript text to visual segment time ranges.

    Takes transcript segments (from VTT/Whisper) and visual segments (from Gemini),
    and assigns the appropriate audio text to each visual segment.

    Returns: updated visual segments with 'audio' field populated.
    """
    from frames import timestamp_to_seconds

    for vis_seg in visual_segments:
        vis_start = timestamp_to_seconds(vis_seg['start'])
        vis_end = timestamp_to_seconds(vis_seg['end'])

        # Collect all transcript text that overlaps this visual segment
        texts = []
        for t_seg in transcript_segments:
            t_start = t_seg.get('start_seconds', timestamp_to_seconds(t_seg['start']))
            t_end = t_seg.get('end_seconds', timestamp_to_seconds(t_seg['end']))

            # Check for overlap
            if t_start < vis_end and t_end > vis_start:
                texts.append(t_seg['text'])

        vis_seg['audio'] = ' '.join(texts) if texts else ''

    return visual_segments
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_avt.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/avt.py tests/test_avt.py
git commit -m "feat: add avt.py format writer and parser"
```

---

## Task 9: analyze.py — Orchestrator

**Files:**
- Create: `scripts/analyze.py`
- Create: `tests/test_analyze.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_analyze.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def test_parse_args_url():
    from analyze import parse_args
    args = parse_args(['https://youtube.com/watch?v=test'])
    assert args.source == 'https://youtube.com/watch?v=test'
    assert args.out_dir == '.'
    assert args.max_frames == 80
    assert args.no_whisper is False


def test_parse_args_local():
    from analyze import parse_args
    args = parse_args(['/path/to/video.mp4', '--out-dir', '/output'])
    assert args.source == '/path/to/video.mp4'
    assert args.out_dir == '/output'


def test_parse_args_flags():
    from analyze import parse_args
    args = parse_args([
        'https://example.com/v',
        '--max-frames', '40',
        '--no-whisper',
        '--low-res',
        '--whisper', 'groq',
    ])
    assert args.max_frames == 40
    assert args.no_whisper is True
    assert args.low_res is True
    assert args.whisper == 'groq'


def test_parse_args_force_long():
    from analyze import parse_args
    args = parse_args(['test.mp4', '--force-long'])
    assert args.force_long is True


def test_get_cache_dir():
    from analyze import get_cache_dir
    d = get_cache_dir()
    assert '.cache/video-analyzer/' in d
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_analyze.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Write analyze.py implementation**

```python
#!/usr/bin/env python3
"""
video-analyzer — Orchestrator
Takes any video URL or local file and produces an .avt file with frames.
"""

import argparse
import os
import shutil
import sys
import uuid
from datetime import datetime

from preflight import preflight_check, check_api_keys, ENV_FILE
from download import download_video
from transcribe import get_transcript
from understand import understand_video
from frames import extract_frames, timestamp_to_seconds
from avt import write_avt, align_transcript_to_segments

CACHE_BASE = os.path.expanduser("~/.cache/video-analyzer")


def parse_args(argv=None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze a video and produce an .avt (Agentic Video Transcript) file.",
    )
    parser.add_argument('source', help="Video URL or local file path")
    parser.add_argument('--out-dir', default='.', help="Output directory (default: current dir)")
    parser.add_argument('--max-frames', type=int, default=80, help="Max frames to extract (default: 80)")
    parser.add_argument('--no-whisper', action='store_true', help="Disable Whisper fallback")
    parser.add_argument('--whisper', choices=['groq', 'openai', 'auto'], default='auto',
                        help="Force Whisper backend")
    parser.add_argument('--low-res', action='store_true', help="Use 256px frame width (vs 512px)")
    parser.add_argument('--force-long', action='store_true', help="Allow videos over 90 minutes")

    return parser.parse_args(argv)


def get_cache_dir() -> str:
    """Create and return a unique cache directory for this run."""
    run_id = str(uuid.uuid4())[:8]
    cache_dir = os.path.join(CACHE_BASE, run_id)
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def main():
    args = parse_args()

    # Preflight check
    status = preflight_check()
    if not status['ready']:
        print("Preflight check failed.", file=sys.stderr)
        if status['missing_binaries']:
            print(f"  Missing binaries: {', '.join(status['missing_binaries'])}", file=sys.stderr)
        if status['missing_required_keys']:
            print(f"  Missing API keys: {', '.join(status['missing_required_keys'])}", file=sys.stderr)
        print("Run: python3 scripts/preflight.py", file=sys.stderr)
        sys.exit(1)

    cache_dir = get_cache_dir()

    try:
        # Step 1: Download
        print("Step 1/5: Downloading video...", file=sys.stderr)
        dl = download_video(args.source, cache_dir)

        # Duration guard
        if dl['duration'] > 5400 and not args.force_long:  # 90 minutes
            print(f"Video is {dl['duration'] // 60} minutes. Use --force-long to proceed.",
                  file=sys.stderr)
            sys.exit(1)

        # File size guard
        video_size = os.path.getsize(dl['video_path'])
        if video_size > 2 * 1024 * 1024 * 1024:
            print(f"Video file too large ({video_size / 1e9:.1f} GB). Max 2 GB.", file=sys.stderr)
            sys.exit(1)

        # Step 2: Transcribe
        print("Step 2/5: Extracting transcript...", file=sys.stderr)
        transcript = get_transcript(
            subtitle_path=dl['subtitle_path'],
            video_path=dl['video_path'],
            whisper_backend=args.whisper,
            no_whisper=args.no_whisper,
        )

        # Step 3: Gemini visual understanding
        print("Step 3/5: Analyzing video with Gemini...", file=sys.stderr)
        api_key = _load_key('GOOGLE_API_KEY', ENV_FILE)
        visual_segments = understand_video(dl['video_path'], api_key)

        # Step 4: Extract frames
        print("Step 4/5: Extracting frames...", file=sys.stderr)
        out_dir = os.path.abspath(args.out_dir)
        width = 256 if args.low_res else 512
        frame_results = extract_frames(
            dl['video_path'], visual_segments, out_dir,
            max_frames=args.max_frames, width=width,
        )

        # Step 5: Assemble .avt file
        print("Step 5/5: Assembling .avt file...", file=sys.stderr)

        # Align transcript to visual segments
        aligned = align_transcript_to_segments(transcript['segments'], visual_segments)

        # Assign frame paths to segments
        frame_map = {}
        for fr in frame_results:
            frame_map[fr['seconds']] = fr['path']

        for seg in aligned:
            seg_seconds = timestamp_to_seconds(seg['start'])
            seg['frame'] = frame_map.get(seg_seconds)

        # Build metadata
        duration_s = dl['duration']
        h = duration_s // 3600
        m = (duration_s % 3600) // 60
        s = duration_s % 60
        duration_fmt = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

        metadata = {
            'title': dl['title'],
            'channel': dl['uploader'],
            'duration': duration_fmt,
            'source': args.source,
            'analyzed': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'model': 'gemini-2.5-flash',
            'frames_extracted': len(frame_results),
            'transcript_source': transcript['source'],
        }

        avt_path = os.path.join(out_dir, f"{dl['slug']}.avt")
        write_avt(metadata, aligned, avt_path)

        # Output final path to stdout
        print(avt_path)
        print(f"\nDone! {len(aligned)} segments, {len(frame_results)} frames.", file=sys.stderr)

    finally:
        # Cleanup temp files
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir, ignore_errors=True)


def _load_key(key_name: str, env_path: str) -> str:
    """Load API key from env file."""
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith(f'{key_name}='):
                return line.split('=', 1)[1].strip()
    raise RuntimeError(f"{key_name} not found in {env_path}")


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_analyze.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/analyze.py tests/test_analyze.py
git commit -m "feat: add analyze.py orchestrator"
```

---

## Task 10: SKILL.md and Commands

**Files:**
- Create: `SKILL.md`
- Create: `commands/analyze.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
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
```

- [ ] **Step 2: Write commands/analyze.md**

```markdown
---
name: analyze
description: Analyze a video and produce an .avt (Agentic Video Transcript) file
allowed-tools: Bash, Read, Write, Glob
---

Analyze the video at `$ARGUMENTS` and produce an .avt file.

## Steps

1. Run preflight check:
   ```bash
   cd /Users/franciscojosejimeneznillardkam/Documents/Frank\ DOCS/Frank\ Projects/video_understanding
   python3 scripts/preflight.py --check
   ```

2. If preflight passes, run the analysis:
   ```bash
   python3 scripts/analyze.py "$ARGUMENTS" --out-dir .
   ```

3. Report the output path and a brief summary of what was found (number of segments, frames extracted, transcript source).
```

- [ ] **Step 3: Commit**

```bash
git add SKILL.md commands/analyze.md
git commit -m "feat: add SKILL.md and /analyze command"
```

---

## Task 11: README.md — Public Repo Documentation

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README.md**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README for public repo"
```

---

## Task 12: End-to-End Integration Test

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test (mocked external services)**

```python
# tests/test_integration.py
"""Integration test — verifies the full pipeline with mocked APIs."""
import json
import os
import sys
import shutil
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')


def test_full_pipeline_local_file(tmp_path, monkeypatch):
    """Full pipeline with a local file, mocked Gemini, captions provided."""
    from avt import parse_avt

    # Setup: create a fake video and subtitle file
    video_path = tmp_path / "test-video.mp4"
    video_path.write_bytes(b'\x00' * 1000)

    subtitle_path = tmp_path / "test-video.en.vtt"
    shutil.copy(os.path.join(FIXTURES, 'sample.vtt'), subtitle_path)

    # Mock download to return our local files
    mock_dl_result = {
        'video_path': str(video_path),
        'subtitle_path': str(subtitle_path),
        'title': 'Test Video Integration',
        'uploader': 'Test Channel',
        'duration': 32,
        'slug': 'test-video-integration',
        'is_local': True,
    }

    # Mock Gemini response
    with open(os.path.join(FIXTURES, 'gemini_response.json'), 'r') as f:
        mock_gemini_segments = json.load(f)

    # Mock frame extraction (no actual ffmpeg)
    mock_frames = [
        {'path': 'frames/frame-001.jpg', 'timestamp': '00:00', 'seconds': 0},
        {'path': 'frames/frame-002.jpg', 'timestamp': '00:04', 'seconds': 4},
        {'path': 'frames/frame-003.jpg', 'timestamp': '00:15', 'seconds': 15},
    ]

    out_dir = tmp_path / "output"
    out_dir.mkdir()
    (out_dir / "frames").mkdir()

    with patch('analyze.download_video', return_value=mock_dl_result), \
         patch('analyze.understand_video', return_value=mock_gemini_segments), \
         patch('analyze.extract_frames', return_value=mock_frames), \
         patch('analyze._load_key', return_value='fake-key'), \
         patch('analyze.preflight_check', return_value={'ready': True, 'missing_binaries': [], 'missing_required_keys': []}):
        # Note: imports are at module level in analyze.py, so patching on 'analyze.*' is correct

        # Run orchestrator with mocked internals
        sys.argv = ['analyze.py', str(video_path), '--out-dir', str(out_dir)]
        from analyze import main
        main()

    # Verify .avt file was created
    avt_path = out_dir / "test-video-integration.avt"
    assert avt_path.exists()

    # Parse and validate
    result = parse_avt(str(avt_path))
    assert result['version'] == '1.0'
    assert result['metadata']['title'] == 'Test Video Integration'
    assert result['metadata']['transcript_source'] == 'captions'
    assert len(result['segments']) == 3
    assert result['segments'][0]['scene'] == 'intro'
```

- [ ] **Step 2: Run the integration test**

Run: `python3 -m pytest tests/test_integration.py -v`
Expected: PASS

- [ ] **Step 3: Run all tests together**

Run: `python3 -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add end-to-end integration test"
```

---

## Task 13: Final Polish and Initial Commit

- [ ] **Step 1: Update .gitignore to include test cache**

Add to existing `.gitignore`:
```
# Test
.pytest_cache/
```

- [ ] **Step 2: Create scripts/prompts/ directory (ensure it exists for understand.txt)**

- [ ] **Step 3: Run full test suite one final time**

Run: `python3 -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: video-analyzer v1.0 — complete implementation"
```

---

## Summary

| Task | Module | Tests | What it delivers |
|------|--------|-------|-----------------|
| 1 | Infrastructure | fixtures | requirements.txt + test data |
| 2 | preflight.py | 5 tests | Dependency checking |
| 3 | download.py | 5 tests | Video acquisition (yt-dlp + local) |
| 4 | transcribe.py | 5 tests | VTT parsing with dedup |
| 5 | whisper.py | 5 tests | Whisper API clients |
| 6 | understand.py | 4 tests | Gemini video analysis |
| 7 | frames.py | 5 tests | ffmpeg frame extraction |
| 8 | avt.py | 6 tests | .avt format read/write |
| 9 | analyze.py | 5 tests | CLI orchestrator |
| 10 | SKILL.md + command | — | Claude Code integration |
| 11 | README.md | — | Public repo documentation |
| 12 | Integration test | 1 test | Full pipeline verification |
| 13 | Polish | — | Final cleanup and commit |
