#!/usr/bin/env bash
# Linux launcher: runs source in place; never modifies or installs anything.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 is required. Install python3 using your distribution package manager." >&2
    exit 1
fi
if ! python3 -c 'import tkinter' >/dev/null 2>&1; then
    echo "Python Tkinter is required. Install python3-tk (Debian/Ubuntu) or python3-tkinter (Fedora)." >&2
    exit 1
fi
if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
    echo "No graphical desktop display detected. Start this from a Linux desktop session." >&2
    exit 1
fi
exec python3 integrated_app.py
