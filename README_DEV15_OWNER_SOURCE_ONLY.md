# Dumbplayer DEV15 — media notification after interruptions; retire saturated-volume seek

**November 11, 2026. SOURCE ONLY.** This is a small, separate candidate continuing the **DEV14 R1** changed-files overlay on top of DEV13 R2 + R3. It has **not** been compiled with the Android SDK, signed, installed, or tested on a Kyocera handset. Do not uninstall or replace the working Dumbplayer. Its playlists, audio, position, bookmarks and existing permanent signing key are untouched.

## Owner observation, not an inferred test

On the actual installed Dumbplayer, two fast Volume Up presses cannot seek backward when the Android music volume is already at maximum; normal volume-down adjustments tend to trigger undesired seeks unless unreasonably slow. With the flip shut/screen off, an incoming text can interrupt playback and require reopening Dumbplayer and pressing Resume. Aurora would prefer quick explicit Play from a headset or a media notification.

## Why these two things happened in the inspected source

**Volume workaround:** `VolumeDoubleTapSeek` watches *changes in `STREAM_MUSIC` volume index*, not physical headset-button events. At a maximum or minimum index, further presses do not change the sampled index. This is a hard observation limit, not a mere debounce issue. Actual Kyocera headset event delivery remains handset-specific and unverified in this candidate.

**Text interruption:** DEV14 already had a `MediaSession`, a foreground media notification and media-button callbacks, but `focusChanged(...)` called `retireForeground()`, which used `stopForeground(true)` and `stopSelf()`. As a result the paused notification was removed and the service could be destroyed. This was source-level evidence of the reported symptom, not an independent on-device SMS reproduction.

## DEV15 changes

1. **Disable double-volume polling in normal release builds**, even if the old `double_volume_seek` preference was saved as `true`. Only `BuildConfig.DEBUG` can activate the old experimental detector. Hide its two settings entries from normal builds, keeping the diagnostic experiment available to explicitly compiled debug editions. **Ordinary volume control remains untouched**. The existing `MediaSession` Play/Pause/Next/Previous transport callbacks remain unchanged, as do 1/3 ±10-second keypad seeks, and separate audiobook/music shuffle.
2. **After an explicit Pause or an audio-focus interruption**, if the service still has a prepared track, keep the `MediaSession` active and publish a visible, *non-ongoing*, paused media notification with Previous / **Play** / Next. Release foreground-service status using `stopForeground(false)` (Android 10); do **not** `stopSelf()` during a normal pause. Keep existing saved position and block automatic playback until the user explicitly requests it.
3. **Notification Play and headset media Play/Play-Pause** use existing MediaSession/notification actions. They request audio focus again, block restart during calls, and restart the existing prepared player only on explicit request. If Android delivers the headset Play event to Dumbplayer's active session, no activity navigation should be necessary. This cannot be guaranteed until checked on the E4831.
4. **Ordinary STOP, unprepared or failed-open player, and actual service destruction** still remove stale notification and release the session. Process death, reboot, forced-stop, and device-specific background restrictions are *not* solved; there is deliberately no autoplay from saved progress after process creation.
5. **For music only**, let Android 10 perform its normal transient notification ducking (`setWillPauseWhenDucked(false)`); **for audiobooks**, continue to request pause-on-duck to avoid losing spoken words. For other focus losses, stay paused with explicit Play notification. Automatic system ducking depends on the other app's focus request and is not promised for every SMS app.
6. VersionCode **18**, versionName `0.2.9-dev15-notification-resume`, unchanged package ID `org.roarin.kyocerakeypad.sandboxwqa365`. This is an uncompiled candidate and not an update ready to install.

## Offline checks and known gaps

- **22 pure-Java core test classes PASS** after compilation with `javac --release 8`. This includes the actual volume-index detector's boundary tests, `AudioFocusGateTests`' no-auto-resume tests, the DEV14 active-playlist mutation checks, transport sequencer and playlist/import/state checks. No Android runtime was involved.
- New **DEV15 static source contracts: 30/30 PASS**; existing DEV14 source contract **23/23**, DEV13 integration **25/25**, Bluetooth debug/volume contracts, stale import and library availability tests all PASS. See `DEV15_TEST_LOG.md` and `tests/run_dev15_source_smoke.sh`.
- The changed Android Java files parsed cleanly using JavaCompiler/JavacTask `parse()`; **syntax parsing is not SDK compilation or Android UI/device execution**.
- Historical test scripts tied to DEV8/DEV9 versions and activity-only playback have inherited or newly-obsolete assertions; `tests/run_bluetooth_volume_seek_smoke.sh` is **not** the correct DEV15 build gate. We have not relabeled those old results as passes. The new workflow runs the targeted DEV15 tests instead.
- **NOT TESTED:** Android Gradle build, target handset notification permission/settings, SMS interruption behavior, foreground service lifetime while paused, actual Bluetooth resume event routing, release signing, safe in-place update, app force-stop/reboot, calls or process-death recovery.

## Optional later build path, without uploading the owner's key

This changed-files ZIP overlays the exact original DEV13 R2 full source plus DEV13 R3 overlay and DEV14 R1 overlay; it is **not** a complete independent repository. The newer optional `.github/workflows/dev15-unsigned-local-sign.yml` is manual-only and would compile an **unsigned** APK after selected regressions when deliberately run by the owner. No workflow was triggered here. Use the owner's already established private signing key **locally** after real build validation and verify signer fingerprint against her installed app; never uninstall to bypass a mismatch. No secret or APK is included.

## Short handset evidence to capture later, at owner's convenience

With a disposable playlist on an eventual approved/dev-signed install: play Music, close flip, trigger one harmless text, check whether music ducks or pauses, whether a paused media notification remains, and whether one headset Play or notification Play resumes. Repeat with an audiobook. During a real call, verify that playback does **not** auto-resume. Check that double volume Up/Down changes volume normally without seeking and media Play/Next/Previous still work. Record exactly what the UI/device does; these are *future optional tests*, not results claimed here.

The original DEV13/DEV14 archives and the currently installed Dumbplayer are preserved; no source was committed to GitHub, no device state changed, and no media was copied or deleted.
