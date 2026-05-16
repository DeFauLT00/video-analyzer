---
name: analyze
description: Analyze a video and produce an .avt (Agentic Video Transcript) file
allowed-tools: Bash, Read, Write, Glob
---

Analyze the video at `$ARGUMENTS` and produce an .avt file.

## Steps

1. Run preflight check:
   ```bash
   cd "$PROJECT_DIR"
   python3 scripts/preflight.py --check
   ```

2. If preflight passes, run the analysis:
   ```bash
   python3 scripts/analyze.py "$ARGUMENTS" --out-dir .
   ```

3. Report the output path and a brief summary of what was found (number of segments, frames extracted, transcript source).
