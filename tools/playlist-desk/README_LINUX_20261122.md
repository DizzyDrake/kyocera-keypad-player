# Playlist Desk — Linux source port (2026-11-22)

**Base requested by owner:** the complete November 15, 2026 integrated Playlist Desk source (`PLAYLIST_DESK_INTEGRATED_SOURCE_20261115.zip`), original SHA-256 `ceaf79e1220ce4b9d40b5ad40dfe5b036cd449d0a048349abb755917ed89deaa`.

**Status:** standalone source ZIP runnable with Python 3 + Tkinter on a Linux desktop. **Not** an AppImage, native .deb/.rpm, installed release, or owner-tested Linux workstation. The original November 15 source and Windows launcher are preserved; this is a separate candidate. The November 15 owner hold on autonomous Playlist Desk/phone-player/Pomodoro queue work is unchanged; this port is a direct owner-requested exception.

## Linux quick start

1. Extract the ZIP into a new folder on your Linux computer, separate from any working Windows installation. Do not extract or run it on a protected drive.
2. Open a terminal **in the extracted folder**, then run:

   ```bash
   cd src
   bash launch_linux.sh
   ```

3. If the launcher says Tkinter is missing, install the native Python/Tk package using your distribution's package manager:
   - Debian / Ubuntu / Linux Mint: `sudo apt install python3 python3-tk`
   - Fedora: `sudo dnf install python3 python3-tkinter`
   - Arch: `sudo pacman -S python tk`

Python 3.9+ and a graphical desktop are required. Tk 8.6 works on X11; on Wayland desktops, XWayland is typically needed. No Python `pip` dependencies or administrator privileges are needed **to run the application** after Python/Tk is installed. `launch_linux.sh` changes only its working directory and starts the GUI; it does not install anything.

## First offline test (fictional data)

In Playlist Desk, select **Load phone snapshot JSON…** and open `src/sample/fictional_phone_snapshot.json`. Try playlist navigation, the Library filter, and saved-plan preview. For Linux file staging, select **Stage PC audio files…** and choose audio files from a normal Linux path (e.g. `/home/you/Music/song.mp3`), if you want to try that feature. Staging **does not open, copy, transfer, or play** audio. It records local path text as **pending, not on phone**; the bridge intentionally refuses phone-plan export until pending files are removed or resolved. Do not use real music or phone writes for the first test.

To run the automated checks from `src` (tests use fictional data and synthetic paths):

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
# GUI tests need a desktop or Xvfb:
PYTHONPATH=. python3 tests/gui_linux_port.py
```

Optional developer checks (if Xvfb installed): `PYTHONPATH=. xvfb-run -a python3 tests/gui_linux_port.py`.

## Preserved functionality

- Existing local-first playlist editor, saved-playlist navigation, comma OR/NOT filter, CSV/M3U rebuilding and offline preview
- Exact local artist-credit matching; optional user-initiated Ollama Gemma4:12b localhost requests (Ollama/model **not** installed or verified by this package)
- Metadata-only *possible* duplicate review; does not prove identical audio and does not delete files
- Optional explicit MusicBrainz lookup (requires internet and user-supplied contact identity; not tested live)
- JSON snapshot, saved plans and simulated exports, with the same provisional phone-bridge schema and safety restrictions
- Original `src/launch_windows.cmd` retained, but **Windows runtime regression not performed in this port session**

## Linux-specific changes (narrow)

- Added executable `src/launch_linux.sh` with Python/Tk and desktop checks.
- `src/pc_file_add.py` now accepts absolute POSIX file paths **as text** while retaining existing Windows drive-path handling; Linux paths are compared case-sensitively, Windows drive paths case-insensitively. F: and conventional `/mnt/f` protected-path text are still rejected.
- `src/integrated_app.py` uses a Linux-friendly font fallback, platform-neutral header wording, and a Linux-compatible `*` all-files chooser filter.
- Added seven Linux path unit tests and a real-Tk Linux staging/save/reopen smoke test.
- No other application runtime `.py` files changed from the November 15 source. See `LINUX_PORT_CHANGES_20261122.patch`.

## Verified and unverified

**Verified in container on Linux:** 249/249 unit tests; 10/10 selected Tk GUI scripts under Xvfb (eight November 15 baseline scripts plus the legacy PC-staging GUI and the new Linux staging GUI); Python compileall; shell syntax; launcher opens and stays alive under Xvfb until bounded timeout; checksum manifest. See `LINUX_PORT_TEST_REPORT_20261122.md`.

**Not verified:** physical Linux desktop/Wayland distro-specific behavior, owner library, actual audio files, real Ollama or MusicBrainz calls, ADB/phone import, Windows regression, native packaging or user acceptance. No real music, phone, protected drive, or owner local filesystem was accessed in producing this port.

## Source integrity and provenance

`python3 VERIFY_INTEGRATED_SOURCE.py` checks the **current Linux-port** `SHA256SUMS.txt`. The original November 15 hash manifest is preserved as `provenance/SHA256SUMS_ORIGINAL_20261115.txt` for historical comparison. Historical `INTEGRATION_MANIFEST_20261115.json` and old README files remain historical; `LINUX_PORT_MANIFEST_20261122.json` is the authoritative port manifest. No Python bytecode, compiled binary, music media, APK, or installer is included.
