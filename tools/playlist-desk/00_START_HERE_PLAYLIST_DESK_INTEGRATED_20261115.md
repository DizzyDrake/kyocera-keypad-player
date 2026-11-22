# Playlist Desk — consolidated integrated source (2026-11-15)

This is a **complete, unpack-and-run source tree**, not a compiled Windows installer, not a phone APK, and not an owner-accepted new release. It consolidates the latest verified November 12 WQB390 source: saved-playlist navigation, comma OR/NOT Library filter, local strict artist-credit/Gemma4 artist-first controls, duplicate-candidate metadata review with bounded 200-row pages, and malformed-track guards. Earlier phone/PC bridge and optional MusicBrainz work are preserved through this exact source lineage.

## Use on Windows (later, when the owner chooses to resume)

1. Keep the existing working Playlist Desk folder untouched.
2. Extract the entire ZIP into **a separate folder outside F:\**.
3. Launch `src\launch_windows.cmd` (requires Windows Python 3 with Tkinter). No pip package was required by the static launch-source audit.
4. For first validation, use `src\sample\fictional_phone_snapshot.json`; do not start by writing to the real music catalog or phone.
5. The owner has explicitly paused further Work Queue work on Playlist Desk and Kyocera player / Dura Pomodoro, effective November 15. This direct handoff is the requested integration, **not a resumption**.

## What's integrated

- November 8 artist-first local matching and strict full-artist-credit checks, optional Gemma4:12b (local model availability untested here)
- November 10 comma syntax with positive-term OR and global NOT expressions **as provisional agent-selected semantics**, not an owner-mandated grammar
- November 10 saved playlist next/previous navigation (including keyboard routes)
- November 10-12 metadata-based *possible* duplicate review with pagination, **not** acoustic identity or automatic file deletion
- November 12 WQC018 malformed metadata guard in actual GUI
- Earlier read-only bridge, import, list selection and optional MusicBrainz candidate source ancestry

## Exact source ancestry

Original latest full merge: `PLAYLIST_DESK_WQB390_GUARDED_WQC013_SOURCE_ONLY.zip`, SHA-256 `098ff15f0269e1ecdce255004629e907dde02ff6db7b2f8c08359202f4b11549`, 95 original ZIP members. Its full application runtime (`src/*.py`, etc.) is **unchanged byte-for-byte** in this packet.

Changed only the stale assertion string in `src/tests/gui_smoke.py` (it expected the old `edits retained` status, while the working GUI now correctly says `playlists are retained`), added two existing Week 2 source-tested GUI regression files (`gui_wqb388_combined_ui.py`, `gui_wqc021_guard.py`), and added these root provenance/checksum files. No new app feature, API change, theme or color change is claimed. See `INTEGRATION_MANIFEST_20261115.json`, `OFFLINE_TEST_REPORT_20261115.md` and the original `README_WQB390_GUARDED_CANDIDATE.md`.

## Test / release limitations

Run `python -m unittest discover -s tests -p "test_*.py"` after `cd src`: 242 unit tests passed in the present Linux environment. Eight separate real-Tk/Xvfb GUI tests passed (including corrected legacy smoke and the imported WQB388/WQC021 tests). Compileall passed. No real Windows application launch, owner catalog, Ollama model, music audio, ADB phone transfer or installation was tested. Preserve original ZIPs and the current owner-installed PC application.

### Known remaining requested refinements

Owner-requested button colors/workflow simplification has **not** been independently verified in this branch. Matching possible duplicates by normalized metadata does not establish acoustically identical recordings or permit deletion. Windows/owner trial remains deferred by queue pause.
