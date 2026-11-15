# DUMBPLAYER — current consolidated GitHub source (DEV16)

**Upload-ready source package | November 15, 2026 | existing versionCode 19.**

This is **one complete repository-root source tree**, not a changed-files overlay. The Android Java application files are byte-for-byte identical to the canonical verified **DEV16 full source** assembled November 11 from DEV13 R2, DEV13 R3, DEV14, DEV15, and DEV16. This repack adds GitHub upload instructions, a Windows push helper, and additional release verification; **it does not claim a new phone feature or a DEV17 Android build.** The original DEV16 source hashes are preserved in `SOURCE_MANIFEST.json`.

## What is integrated

- **DEV13:** double Volume Down seeks +30s / double Volume Up −15s as a configurable *experimental* mode; stale PC playlist imports with preview, missing-track handling, safe reference rescan and cleanup, and export unaffected by missing/renamed audio IDs. This experimental volume-index monitor is OFF by default in ordinary builds following DEV15.
- **DEV14:** independent music/book shuffle and playback order, active playing-playlist browser, select track or remove playlist entry including currently playing entry without deleting the audio, menu navigation while playback continues, easy return to Now Playing.
- **DEV15:** paused media notification and explicit headset Play after an interruption; no unrequested automatic playback resume; unreliable background volume polling disabled in ordinary builds.
- **DEV16:** audiobook Bluetooth/media Previous/Next −15/+30 seconds by default; music defaults to previous/next tracks. Both behaviors have independent persistent toggles in Listening Settings plus a current-lane quick toggle on Now Playing. Local [4]/[6] remain track navigation.

**GitHub repository identity:** `org.roarin.kyocerakeypad.sandboxwqa365` / `versionCode 19`, `versionName 0.3.0-dev16-remote-skip`. No additional application, no alternate signing identity, and no audio, database, private key, playlist export, or token bundled.

## Simplest upload (Windows with Git installed)

1. Extract the ZIP **completely**. The extracted root contains `app`, `tests`, `.github`, `settings.gradle`, and `build.gradle` — do not upload the ZIP as a single file and do not nest everything under an extra directory in the GitHub repo.
2. Double-click `UPLOAD_TO_EXISTING_GITHUB.cmd`, enter the URL of **your existing Dumbplayer repository** (`https://github.com/<owner>/<repo>.git`). It clones a temporary checkout, overlays this full source tree, displays changed paths, and asks before committing/pushing. No force-push, deletion of unrelated repository files, signing material, or modification of the installed phone.
3. On GitHub: **Actions** → **Dumbplayer DEV16 unsigned candidate (local signing required)** → **Run workflow**. Use the branch with the upload. The workflow runs the offline regression and an Android 33 / Java 17 / Gradle 7.6.4 release build.
4. Download the job's `dumbplayer-dev16-UNSIGNED-LOCAL-SIGNING-REQUIRED` artifact. This is an **unsigned** release APK. Sign locally with the existing permanent Dumbplayer signing key, then install as an update only after its certificate matches the installed app. The permanent signer certificate SHA-256 is `C0:A3:09:29:88:3D:4E:56:13:5F:40:21:93:BB:3A:D4:12:8F:31:22:97:44:06:B3:CF:EE:9A:B6:D8:4A:3B:8C`.

If you prefer manual upload through GitHub's browser, it permits at most 100 files per upload, so this ~150-file tree must be uploaded in multiple groups while retaining directory paths. Using the Git helper avoids missing `.github/workflows` or nested source files. If the repository's GitHub files have since diverged from the source tree, inspect the status preview carefully rather than assuming it matches.

## Self-checks performed here

- Original `WQ439_VERIFY_FULL_SOURCE.py`: 145 original DEV16 source SHA-256 checks and 3 packaged-source checks **PASS**.
- `bash tests/run_dev16_source_smoke.sh`: pure-Java policy and source-wiring checks **PASS**.
- `python VERIFY_UPLOAD_READY_DEV16.py`: full package features/manifest/workflow verification **PASS**.
- Fresh ZIP extraction, file SHA-256 and ZIP CRC independently checked **PASS**.

**Not claimed:** GitHub repository inspection or upload, GitHub Actions run, Android SDK compilation, APK signing, signed installation, Bluetooth/closed-flip/SMS physical verification. The connected GitHub tool returned no accessible repositories during this pass. The app's Java source is unchanged from DEV16.

## Relevant files

- `.github/workflows/dev16-unsigned-local-sign.yml` — **current workflow**; other `dev13-*`, `dev14-*`, and `dev15-*` workflows are **historical**, retained for provenance. Choose DEV16.
- `README_DEV16_OWNER_SOURCE_ONLY.md` — DEV16 behavior and testing record.
- `WQ439_READ_FIRST_FULL_SOURCE.md` — the underlying 2026-11-11 full-source consolidation provenance.
- `WQ439_VERIFY_FULL_SOURCE.py` — original original-source cryptographic verification.
- `VERIFY_UPLOAD_READY_DEV16.py` — new packaging and workflow check.
- `UPLOAD_TO_EXISTING_GITHUB.cmd` / `PUSH_DEV16_TO_GITHUB.ps1` — optional Git-based full-tree upload helper.
- `README.md` — **historical DEV13 record**, not current release directions.

No files in the existing Android app source, manifests, `.github` workflows, or original original-source manifests were changed by this upload-ready repack.
