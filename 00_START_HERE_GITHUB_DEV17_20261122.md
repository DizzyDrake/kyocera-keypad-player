# Dumbplayer DEV17 — complete GitHub Actions source handoff

**Owner-requested integrated source candidate, 2026-11-22.** This contains a full
Android app project; it is NOT a patch and NOT a compiled APK.

## Upload to existing repository (Windows)

1. Extract the **whole ZIP** so you see `app/`, `tests/`, `.github/`, `settings.gradle`,
   `build.gradle`, `README.md`, and `UPLOAD_TO_EXISTING_GITHUB.cmd` at the *same level*.
2. Preserve the old repository state in GitHub (it has its own commit history).
3. Double-click `UPLOAD_TO_EXISTING_GITHUB.cmd` to clone and overlay the updated
   files. Enter the exact existing repository HTTPS URL. Review the printed `git status`
   before typing `yes` to commit and push; decline if the wrong repository appears.
   The helper never force-pushes or uninstalls/deletes existing phone data. The helper
   copies files but does not intentionally delete older unrelated repository files.
   Alternatively, upload the **contents of the extracted ZIP**, maintaining paths
   such as `.github/workflows/dev17-unsigned-local-sign.yml` (do not upload the
   unopened ZIP as a single file and expect GitHub Actions to compile its contents).
4. In the repository **Actions** page, select
   `Dumbplayer DEV17 integrated unsigned candidate (local signing required)`
   and click **Run workflow**. Ensure GitHub Actions is enabled for that repository.
5. On success, download the `dumbplayer-dev17-UNSIGNED-LOCAL-SIGNING-REQUIRED`
   artifact. The `.apk` inside is unsigned, not ready to install as an update.

This GitHub Actions workflow has Java 17, Gradle 7.6.4, Android SDK 33 and
build-tools 33.0.2, and performs host-side source tests before `:app:assembleRelease`.
There is **no APK signing key in this ZIP or GitHub Actions**.

## Sign safely on your PC

Use the Android SDK `zipalign` and `apksigner` tools with your already established
private **permanent DEV13–16 signing key**, not a freshly created key. Check the
**expected existing certificate SHA-256** before any install:

`C0:A3:09:29:88:3D:4E:56:13:5F:40:21:93:BB:3A:D4:12:8F:31:22:97:44:06:B3:CF:EE:9A:B6:D8:4A:3B:8C`

`zipalign -p -f 4 app-release-unsigned.apk app-release-aligned.apk`

`apksigner sign --ks PATH_TO_OWNER_KEYSTORE --ks-key-alias OWNER_ALIAS --out dumbplayer-dev17-signed.apk app-release-aligned.apk`

`apksigner verify --verbose --print-certs dumbplayer-dev17-signed.apk`

Only if its signer matches the **installed APK** and the application ID is
`org.roarin.kyocerakeypad.sandboxwqa365` with versionCode **20**, update with
`adb install -r dumbplayer-dev17-signed.apk`. On any incompatibility error,
**stop**; do not uninstall or clear data. This is a source handoff, NOT a request
for you to install before inspecting the result.

## What changed (source only)

- Replaced `stopPlayer()` during track-to-track transitions with a distinct
  foreground-preserving `releaseForTrackHandoff()`; keeps a single MediaPlayer.
- Short audio-focus loss may resume only the *previously playing* music or
  audiobook session on a matching focus GAIN. Explicit pause/stop and permanent
  focus loss cannot automatically resume. Android call detection is an
  OEM-dependent risk requiring real-phone testing.
- Avoid starting audio before an asynchronous resume seek finishes.
- Preserve existing separate music/book shuffle, remote Next/Previous settings,
  playlist browsing/removal, stable playback identity, app-private data.
- Orange Music, navy Audiobooks, visually neutral shared screens, with labels
  independent of color. New adaptive launcher icon from Nov 18 Library artwork.

Host test command (Linux, Git Bash or WSL): `bash tests/run_dev17_source_smoke.sh`.
`tests/test_dev15_interrupted_notification.py` and historical DEV16 manifests
remain retained as **historical evidence**: the old DEV15 test intentionally
assumes focus GAIN never auto-resumes, which the owner has since changed.
**Do not run the historical DEV16 full-source hash verifier as a DEV17 test**,
because DEV17 intentionally changes code and Gradle version metadata.

## Evidence / caveats

Reproducible tests and hash manifest are in `DEV17_TEST_RESULTS.json` and
`DEV17_SHA256_MANIFEST.json`. Java core checks + source checks establish source
consistency, not actual Android API correctness, signing, device compatibility,
audio focus callback behavior, closed-flip background continuity, or field acceptance.
No confidential keystore, phone audio, playlist data, or account credentials included.
The original untouched DEV16 GitHub package remains in the ChatGPT Library.
