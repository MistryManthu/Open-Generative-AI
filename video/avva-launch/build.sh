#!/usr/bin/env bash
# Rebuilds both launch videos from audio/timing.json (run make_audio.py first).
cd "$(dirname "$0")" && python3 build.py
