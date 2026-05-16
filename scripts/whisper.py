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
    from transcribe import format_timestamp
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
    from transcribe import format_timestamp
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
