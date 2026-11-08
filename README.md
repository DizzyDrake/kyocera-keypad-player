# Dumbplayer DEV13 — playlist import and Bluetooth owner trial

**2026-11-08 source candidate only.** Derived from archived DEV12, preserving original source and existing WQA365 package identity. No phone installation, APK compilation, APK signing, or on-device DEV13 tests were performed for this bundle.

## Owner-selected behavior integrated

- **Double Volume Down: forward 30 seconds**; **double Volume Up: back 15 seconds** while playing. Normal single-press volume changes continue; incidental volume changes on double presses are acceptable. The experimental setting remains user-selectable in Listening settings. Existing settings/preferences persist on compatible in-place update. Because input is inferred from sampled volume-level changes, the phone's own volume buttons can also trigger seeks, and the endpoints may not be detected.
- Home title derives `DEV13` from Gradle `BuildConfig.VERSION_NAME`; no leftover `DEV10 Import Trial` banner.
- `Import PC playlists (ADB transfer)` requires the `kyocera-playlist-import-v0.1` schema and the exact filename `pc_playlist_import_v1.json` in this app's external `transfer` folder. Stale or missing `expected_snapshot_id` is allowed with a clear warning. File structure and duplicate track/playlist identities still validated.
- Import preview lists how many available/missing track references are found. Missing IDs are skipped; original relative playlist and track order, names, audiobook flags, and empty playlists are retained. User must confirm **Replace playlists**; preflight does not stop playback. After confirmation, all existing playlist definitions are replaced; usable bookmarks and audio remain untouched; valid resume state retained when possible.
- Caution: Android can reassign a content media ID to different audio. A stale import can therefore include the *wrong* file for an ID that still exists. The preview cannot automatically prove identity; do not claim it does.

## DEV12 compatibility and safe signing

This source keeps applicationId `org.roarin.kyocerakeypad.sandboxwqa365` and bumps versionCode **15 → 16**; versionName `0.2.7-dev13-stale-import-bt-direction`. Both version and package are necessary but not sufficient for update. Android **requires a matching signing certificate**.

The owner-supplied `app-debug.apk` of DEV12 was independently inspected for its embedded APK Signature Scheme v2 signer certificate:

`C7F55F72049E0547354F65816836856735124AB9B46AC73A0265AF099FEFAC16` (SHA-256)

The APK's certificate is public. **Its corresponding private signing key is not recoverable from the APK.** The certificate `not_before` was `2026-11-08T21:20:53Z`; the development build may have used a newly generated ephemeral GitHub Actions debug key. Merely building this source in a new GitHub Actions runner can create a different signing key and **cannot be assumed to update DEV12**.

Two GitHub Actions workflows in `.github/workflows/`:

1. `dev13-compile-check.yml`: Build and run tests; intentionally uploads **no APK**.
2. `dev13-update-signed.yml`: Build **unsigned release**, sign with a GitHub Secrets keystore, verify APK signature, enforce the expected DEV12 certificate, application ID and versionCode 16, **then** upload the update APK. On mismatch/missing secret, the workflow fails rather than deliver an incompatible installer.

For the second workflow, the repository owner must possess the **original DEV12 private signing key** and configure these GitHub repository *Actions secrets* (do not paste secrets into chats/logs):

- `KYOCERA_DEV12_KEYSTORE_BASE64`: base64 of the original Java keystore bytes, generated privately and uploaded as GitHub secret
- `KYOCERA_DEV12_KEYSTORE_PASSWORD`
- `KYOCERA_DEV12_KEY_ALIAS`
- `KYOCERA_DEV12_KEY_PASSWORD`

If the original key was generated on a disposable runner and not backed up, **we cannot promise an in-place update**. Do not uninstall, clear data, or replace the installed app on that basis. Revisit owner-approved backup/migration separately. An installed DEV12 backup APK alone does not contain the needed private key.

After the signed workflow succeeds, use `adb install -r "path/to/dumbplayer-dev13-update-candidate.apk"`; `-r` requests an update retaining app data. On `INSTALL_FAILED_UPDATE_INCOMPATIBLE`, stop and preserve installed DEV12, then report the error. Do not uninstall to force a signature change.

## What was tested here

See `DEV13_TEST_REPORT.json` and `DEV12_TO_DEV13.patch` in the root. Offline Java and static source checks can pass without an Android SDK. SDK/Gradle APK compile, GitHub secrets, signing with owner key, device installation, playback/seek, and imports on physical phone remain **unverified** until run by the owner.

## Build inputs / ownership

- Android SDK 33, build-tools 33.0.2, Java 17, Gradle 7.6.4 (GitHub workflow provisions them).
- Previous DEV12 ZIP and stale-import WIP patch remain separately preserved in the ChatGPT Library project.
- No private playlists, audio files, device logs, APK, keystore, or account credentials are bundled in this source ZIP.
- Parent Work Queue: `WQ-20261023-137`. This is one integration continuation, not a new parent task.
