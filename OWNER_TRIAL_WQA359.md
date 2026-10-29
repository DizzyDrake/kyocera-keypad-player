# Keypad Music Player — optional WQA359 async rollback guard (source only)

**Frozen parent:** WQA357 v0.1.7, SHA-256 `76f8059fa58505cc04e0f83af29d99dd6edb7ebabc6c958b19ef1f1ffef42f63`.
**Status:** optional source integration, not a new owner-accepted version, APK, Android compile, or installation.

This candidate changes only pre-prepare media-open rollback. A delayed error can occur after a successful playlist edit. Instead of writing the old playback snapshot unconditionally, the code checks that the failed pending selection is still current and that the old selection still exists. It copies the latest state, saves the copy, and publishes only after a successful write. Newer bookmark edits are preserved. When the old track was removed, rollback is skipped rather than recreating an invalid selection.

**Correction to earlier review:** the specific deletion sequence suggested by WQE084 is not reachable through the current built-in Delete playlist action because that action calls `stopPlayer()` before committing deletion, detaching the player. A closely related Remove track path does not detach a pending player; a late error there can restore a removed track. The baseline regression reproduces this reachable source ordering with fictional state. Real Android callback timing remains untested.

To test offline on a development machine with Java and Python: extract the ZIP, then run `bash tests/run_core_tests.sh` (or run the Java/Python test commands in that script). The Android app requires an Android SDK/Gradle build and owner-supervised E4831 disposable-media testing. No APK is provided. The Gradle version label remains inherited v0.1.7; the WQA359 name is an explicit source-candidate identifier, not a release version.

**Known limitation:** if the old track has been removed, the failed pending selection is retained rather than replaced with a different track or cleared. This is fail-closed against orphaned rollback but may require user re-selection. No automatic title-based substitution, telephony permission, or background service is introduced. Incoming-call pause, physical keypad, AtomicFile behavior, and Android MediaPlayer ordering still need owner-controlled testing.
