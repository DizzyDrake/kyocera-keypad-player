# Offline verification — Playlist Desk Linux source port (2026-11-22)

**Exact parent:** `PLAYLIST_DESK_INTEGRATED_SOURCE_20261115.zip` (186,610 bytes, SHA-256 `ceaf79e1220ce4b9d40b5ad40dfe5b036cd449d0a048349abb755917ed89deaa`). This parent was read from the Library and hash-verified before editing.

**Port scope:** `src/pc_file_add.py`, `src/integrated_app.py`, new `src/launch_linux.sh`, new `src/tests/test_linux_port.py`, new `src/tests/gui_linux_port.py`, plus documentation/manifest. No other existing runtime Python module modified.

**Tests executed on Linux with Python3 and Tk8.6:**
- `python3 -m unittest discover -s tests -p 'test_*.py' -q` from `src`: **249 PASS** (242 inherited + seven new).
- Xvfb/Tk scripts **10 PASS**: `gui_smoke.py`, `gui_comma_filter_wqmanual.py`, `gui_wqb388_combined_ui.py`, `gui_wqc021_guard.py`, `gui_artist_first_guard.py`, `gui_wqa321_navigation.py`, `gui_wqb458.py`, `gui_wqd166_musicbrainz.py`, `gui_wqd137.py`, `gui_linux_port.py`.
- `python3 -m compileall -q .`: PASS.
- `bash -n src/launch_linux.sh`: PASS.
- With `DISPLAY`/`WAYLAND_DISPLAY` unset, Linux launcher exited 1 with a useful no-desktop message: PASS.
- `timeout 3s xvfb-run -a bash src/launch_linux.sh` after changing to `src`: app started without stdout/stderr errors and stayed open until timeout (exit 124): **bounded launch smoke PASS**, not a full interactive human test.
- Synthetic POSIX audio paths were never opened or stat'd; fake phone snapshot SHA remained unchanged; save/reopen exercised only temporary JSON.

**Not tested:** real owner music files, actual Linux desktop session or distro packaging, real Ollama or MusicBrainz network, USB/ADB, phone app, Windows native launch, installed deployment or owner acceptance. **No audio duplicate deletion or playback**.

**Integrity:** current source manifest generated after tests; fresh extraction and checksum verification to be recorded in close-out receipt. Original November 15 SHA256SUMS preserved as provenance. No claims about unchanged Windows behavior beyond passing inherited synthetic tests.
