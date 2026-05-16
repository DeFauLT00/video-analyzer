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
