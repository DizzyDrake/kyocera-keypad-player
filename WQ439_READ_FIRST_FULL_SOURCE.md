# Dumbplayer DEV16 — FULL GitHub source (single ZIP)

**November 11, 2026 — WQ-20261111-439, manual Q, complete source packaging only.**
This one ZIP replaces the need to manually apply DEV13 R2, R3, DEV14, DEV15 and DEV16 **source overlays**. The app source itself is **byte-for-byte unchanged** from the verified DEV16 R1 state. Parent changed-files archives are retained separately in Aurora's Library.

## What's included

- Complete GitHub repository-relative source tree with `app/`, `tests/`, `build.gradle`, `settings.gradle`, `.github/workflows/`, and inherited provenance/license files.
- Existing `SOURCE_MANIFEST.json` for the 145 verified original source files (excludes itself).
- `WQ439_VERIFY_FULL_SOURCE.py` to check all 145 files and original manifest after unpacking (standard Python 3, no dependencies).
- `WQ439_FULL_PACKAGE_MANIFEST.json` binding the five exact source ZIP parents and this package's files.

## Inspect or build later (optional; nothing required tonight)

1. Extract this ZIP into a **new empty directory**. Do not place it over an installed APK, active audio/playlist data, or a different GitHub branch. Don't extract onto protected F: storage.
2. Verify on a computer with Python 3: `python WQ439_VERIFY_FULL_SOURCE.py`. On Windows, `py -3 WQ439_VERIFY_FULL_SOURCE.py`.
3. Optional Java-only regression: `bash tests/run_dev16_source_smoke.sh` (requires Java/Javac 17+ and Python 3; this checks source and pure Java only).
4. The included `.github/workflows/dev16-unsigned-local-sign.yml` is **manual trigger only** for future CI on a GitHub repository whose source matches this tree. Its output is **unsigned** and **not installable**. No workflow was triggered in this session. Local APK signing later must use Aurora's **existing DEV13 permanent signing key**, not previous DEV12 signer; confirm certificate SHA-256 and package ID before any in-place installation.

## The behavior from the owner-approved source sequence

DEV14: separate shuffle, Now Playing playlist navigation, remove-from-playlist (without file deletion), leave menu without pausing.
DEV15: retain paused media notification and headset Play after interruption, ordinary release disable of unreliable volume-index double tap.
DEV16: headset Previous/Next default -15/+30 seconds in audiobooks; normal track navigation default in music; two independently stored settings and Now Playing quick toggle; local keypad [4]/[6] still navigate tracks.

**Not performed:** Android SDK compilation, signed APK creation, Kyocera/closed-flip/SMS/device acceptance, GitHub upload, owner-drive access, live changes, or background automation. Source tests do not establish runtime behavior. Keep Aurora's working installed version untouched.

**Scope note:** The included older README files and historical release workflows are retained for source provenance. Use the DEV16 README/workflow as the current candidate, not DEV13 or older guides. No signing private key, keystore, credential, APK, or user audio/playlists are contained in this ZIP.
