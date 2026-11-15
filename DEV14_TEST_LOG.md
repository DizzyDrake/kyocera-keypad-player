# DEV14 — reproducible source-only verification

**Date:** 2026-11-11. All executions in a Linux sandbox on fictional in-memory Java playlists and archived source. Neither Android APK compilation nor physical Kyocera UI/playback tests were run.

## Passed in final working-source candidate

- `sh tests/run_bluetooth_volume_seek_smoke.sh` — exit 0 (inherited Bluetooth, imports, library cleanup; revised static expectations).
- `sh tests/run_dev9_feature_smoke.sh` — exit 0 (inherited playlist, Now Playing, Home/Move Mode regressions; revised static expectations).
- `python3 tests/test_stale_import_source.py` — 15/15 source checks.
- `python3 tests/test_dev13_integration_source.py` — 25/25 source checks.
- `python3 tests/test_library_availability_source.py` — 14/14 source checks.
- `python3 tests/test_service_lifecycle_source.py` — 9/9 source checks.
- `python3 tests/test_dev14_active_playlist_source.py` — 23/23 source checks.
- `java -cp .build ActivePlaylistEditTests` — 27/27 pure-Java planning/transaction assertions.
- `javac --release 8` full pure-Java core/`tests/*Tests.java` — completed successfully.
- `python -m compileall -q tests` — completed.

## Initial findings and corrections

- First inherited playback regression runs failed because the **original tests explicitly required** a single `shuffle` key and “Back/Home pauses” behavior, both superseded by the owner's new feature request. Their current-source copies were updated to check separate shuffle and nonpausing navigation. The Library-pinned DEV13 R2/R3 original source archives remain preserved.
- One subsequent test still expected the prior Now Playing footer exact string; revised to require the new Back/menu hint.
- One Bluetooth source test expected the old DEV13 version string; revised for DEV14. It still verifies double-VOLUME handling and private-recording debug visibility.
- Legacy `sh tests/run_core_tests.sh` **fails** at `tests/check_android_source_guard.py`; this script expected old activity-owned player callbacks, legacy permissions and explicit pause-on-Back. The DEV13 R3 README already recorded this inherited architectural-guard failure; it is NOT counted as a clean inherited suite. Preserve its failure rather than rewriting historical architectural assumptions just to claim green.

## Key unverified questions

- Android Gradle/SDK compilation, resource binding, exact target device D-pad/focus and Activity lifecycle, app package update signing/certificate, actual MediaPlayer transition after removing current entry, resume behavior across process death, and user acceptance all remain **NOT TESTED**.
- The `dev14-unsigned-local-sign.yml` workflow was prepared but **not run**. No real APK, keys, actual audio or playlist records accessed or changed.
