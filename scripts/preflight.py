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
