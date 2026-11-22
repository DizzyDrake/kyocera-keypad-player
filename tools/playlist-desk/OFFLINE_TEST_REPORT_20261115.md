# Playlist Desk integrated candidate — offline verification report

**Date:** 2026-11-15 CST. **Mode:** owner-directed; source-only. **Base:** WQB390 guarded WQC013, SHA-256 `098ff15f0269e1ecdce255004629e907dde02ff6db7b2f8c08359202f4b11549`.

- Original WQB390 archive integrity and SHA-256: PASS.
- Baseline `src` Python compileall: PASS.
- `python -m unittest discover -s tests -p 'test_*.py'` from `src`: **242 tests PASS** (observed 2026-11-15).
- Eight Tk/Xvfb GUI scripts PASS with `PYTHONPATH=src`: `gui_smoke.py`, `gui_comma_filter_wqmanual.py`, `gui_wqb388_combined_ui.py`, `gui_wqc021_guard.py`, `gui_artist_first_guard.py`, `gui_wqa321_navigation.py`, `gui_wqb458.py`, and `gui_wqd166_musicbrainz.py`.
- Historical GUI smoke `gui_smoke.py` initially failed only a stale status-text expectation (`edits retained`); the actual playlist order and phone snapshot assertions passed. Test was updated to expect the current `playlists are retained` label; rerun PASS. **No runtime source modified.**
- WQB388 GUI and WQC021 guard checks were previously independent Week 2 Library scripts and were integrated under `src/tests/`; both independently reran PASS here.
- Checksum and no-executable-artifacts/ZIP integrity: verified after fresh archive extraction (see package's `VERIFY_INTEGRATED_SOURCE.py`).

**Not verified:** Windows 10 launch, owner's real playlist/csv/catalog, current installed PC version, Gemma/Ollama availability, MusicBrainz internet endpoint, headset or phone, audio duplicates, user acceptance. Status `INTEGRATED_SOURCE_TESTED_OFFLINE / NOT_INSTALLED_OR_OWNER_ACCEPTED`.
