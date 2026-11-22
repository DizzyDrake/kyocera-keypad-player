# Dumbplayer DEV17 — integrated Android source candidate

**Latest complete GitHub Actions source handoff: 2026-11-22.** Start with
[`00_START_HERE_GITHUB_DEV17_20261122.md`](00_START_HERE_GITHUB_DEV17_20261122.md).

VersionCode **20**, package **`org.roarin.kyocerakeypad.sandboxwqa365`**. Source-only;
this ZIP was **not signed, installed or tested on the physical Kyocera**.

Added since verified DEV16: continuity across shuffled track transitions while flip closed,
transient notification-focus pause/resume for **both Music and Audiobooks** (explicit
Pause/Stop never resumes automatically), orange Music / navy Audiobooks UI,
owner-defined navy/orange/white outlined adaptive icon, host regression checks,
and a DEV17 unsigned GitHub Actions build workflow. Real call/notification events
and closed-flip behavior must be tested on the target device.

**To compile**: extract/copy this source to the root of the existing GitHub repository,
then use **Actions → Dumbplayer DEV17 integrated unsigned candidate → Run workflow**.
The workflow deliberately makes an *unsigned* APK; sign **locally** with the same
permanent key used for the installed app, checking the signer before `adb install -r`.
Do not uninstall the installed app to solve signature mismatches.

The historical DEV13 README is retained below as source provenance, not current instructions.

---

## Historical DEV13 README (not the current source release)

# Dumbplayer DEV13 — playlist import and Bluetooth owner trial

**2026-11-08 source candidate only.** Derived from archived DEV12, preserving original source and existing WQA365 package identity. No phone installation, APK compilation, APK signing, or on-device DEV13 tests were performed for this bundle.

## Owner-selected behavior integrated

- **Double Volume Down: forward 30 seconds**; **double Volume Up: back 15 seconds** while playing. Normal single-press volume changes continue; incidental volume changes on double presses are acceptable. The experimental setting remains user-selectable in Listening settings. Existing settings/preferences persist on compatible in-place update. Because input is inferred from sampled volume-level changes, the phone's own volume buttons can also trigger seeks, and the endpoints may not be detected.
- The DEV11 diagnostic still records Bluetooth media events and music-volume index changes during a manually selected 45-second recording; it is independent of the experimental double-volume seek setting.
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

## DEV13 R3: current-library snapshot + explicit unavailable-reference cleanup (November 8, 2026)

- **Export metadata for PC** now builds a **detached** export view using only safe
  track IDs observed by the latest audio scan. Old or changed MediaStore IDs,
  playlist references, orphan bookmarks, and invalid playback contexts are omitted
  **from the exported JSON only**, with counts in the confirmation/result.
  Saved playlists and physical audio files are not deleted by export.
- **Listening settings → Rescan local audio** refreshes the phone's observation.
- **Listening settings → Review / clear unavailable audio references** gives a
  counts-and-consequences confirmation before deleting stale saved references.
  The app keeps playlist names and remaining track order, and never deletes audio.
  A temporarily disconnected/unscanned file can look unavailable; rescan first.
- **Browse/search local audio** hides unavailable entries. Saved playlists still
  display unavailable placeholders until explicit cleanup.
- **Import PC playlists** accepts stale snapshot IDs and checks incoming track
  identities against the *currently observed* usable IDs, skipping missing IDs
  with a warning. Filename remains exactly `pc_playlist_import_v1.json`.
- Playlist Desk v0.16 (and compatible derivatives) can reattach old edited
  playlists to a fresh phone snapshot using matching relative audio paths. Rename
  or move a file and that exact-path reattachment may fail; no speculative title
  matching occurs.

### DEV13 first installation after DEV12 (owner chose blank slate)

The original DEV12 debug certificate differs from Aurora's new permanent signing
certificate `C0:A3:09:29:88:3D:4E:56:13:5F:40:21:93:BB:3A:D4:12:8F:31:22:97:44:06:B3:CF:EE:9A:B6:D8:4A:3B:8C`.
**Do not use** `dev13-update-signed.yml` with a substitute key: it deliberately
checks the *old* DEV12 certificate. For the clean DEV13 installation, use
`.github/workflows/dev13-first-install-unsigned.yml` to build and download an
**UNSIGNED, NOT INSTALLABLE** APK, then sign it locally with the new permanent key
using Android SDK build-tools (`zipalign` and `apksigner`). Verify the new
certificate before installation. Android will not install it over DEV12 because
signatures differ. Before uninstalling DEV12, retain the independently backed-up
private-state TAR (owner-reported SHA-256
`7103B9B89D15018842F67FD5354772DF752B70B5E7DD8BCB60F7B99BC7AC6306`)
and external transfer folder. A fresh install intentionally starts without DEV12
app data; saved Bridge JSON can be imported afterward. Do not commit or upload
signing keystores or passwords. Subsequent builds should reuse this same key.

**Verification scope:** Pure-Java and static source tests pass; this change has
not been Android SDK-compiled or tested on the physical Kyocera in this session.
