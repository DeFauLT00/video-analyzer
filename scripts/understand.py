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
    text = raw_text.strip()
    if text.startswith('```'):
        lines = text.split('\n')
        lines = [l for l in lines if not l.strip().startswith('```')]
        text = '\n'.join(lines)

    segments = json.loads(text)
    return validate_segments(segments)


def understand_video(video_path: str, api_key: str,
                     start_time: str = None, end_time: str = None) -> list:
    """
    Upload video to Gemini and get structured visual analysis.

    Args:
        video_path: Path to video file
        api_key: Gemini API key
        start_time: Optional start time to focus on (MM:SS or HH:MM:SS)
        end_time: Optional end time to focus on (MM:SS or HH:MM:SS)

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
        if start_time or end_time:
            range_str = f" Focus ONLY on the section from {start_time or '0:00'} to {end_time or 'the end'}. Ignore content outside this range."
            prompt += range_str

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
