#!/bin/sh
# Standalone macOS Finder/Terminal launcher for Chess & Chains outside IDEs.
HERE="$(cd "$(dirname "$0")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
    exec python3 "$HERE/start_chess_and_chains.py" "$@"
elif [ -x "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3" ]; then
    exec "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3" "$HERE/start_chess_and_chains.py" "$@"
else
    echo "Python 3 not found. Please install Python 3.11+ with Tk." >&2
    exit 1
fi
