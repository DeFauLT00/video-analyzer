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
                   max_frames: int = 80, width: int = 512,
                   slug: str = None) -> list:
    """
    Extract JPEG frames at segment start timestamps.

    Args:
        video_path: Path to video file
        segments: List of dicts with 'start' key (from understand.py)
        output_dir: Directory to write frames into
        max_frames: Maximum number of frames to extract
        width: Frame width in pixels
        slug: Video slug for namespaced frames directory

    Returns:
        List of {'path': str, 'timestamp': str, 'seconds': float}
    """
    if slug:
        frames_dirname = f"{slug}-frames"
    else:
        frames_dirname = 'frames'
    frames_dir = os.path.join(output_dir, frames_dirname)
    os.makedirs(frames_dir, exist_ok=True)

    all_timestamps = []
    for seg in segments:
        seconds = timestamp_to_seconds(seg['start'])
        all_timestamps.append(seconds)

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

        relative_path = os.path.join(frames_dirname, filename)
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
