# Kyocera Keypad Player DEV6 v0.2.0 — WQB428 source candidate

**Status:** Versioned Android source project only. **Not compiled into an APK, not installed, not tested on the physical Kyocera E4831.** It extends the B-owned DEV5 v0.1.9 source while preserving the owner-tested DEV4 v0.1.8 as the known physical fallback. Parent DEV5 ZIP remains unchanged. This is an incremental experimental build candidate, not a final release.

## New requested features

**Sleep timer (Music and Audiobook Now Playing):** Choose Off/Cancel, 10, 15, 30 or 60 minutes, or enter a custom positive integer number of minutes. Remaining minutes are shown in the Now Playing row and updated footer. Setting again resets the one-shot countdown. On expiry, the playback service pauses and attempts a durable position save, without deleting or resetting tracks, playlists or bookmarks. The countdown uses `SystemClock.elapsedRealtime()` and a service-side Handler while the playback service is alive; the player has a partial wake lock while playing. It follows track changes within the same playlist and is canceled when selecting a different playlist or switching between Music and Audiobook. The timer is deliberately not restored after process death, to avoid an old countdown unexpectedly affecting a new session. This latter choice and behavior during manual pause are provisional, because the owner has not fixed those semantics. **Real flip-closed/screen-off timer reliability is not yet verified.**

**Audiobook resume rewind:** Home → Listening settings cycles **Off (default) → 5 seconds → 10 seconds → Off**. It affects only explicit Resume audiobook, not Music, normal track selection, bookmark jumps or the existing manual Back 10 seconds action. The saved position remains the canonical value until the resumed player actually starts; the requested audible offset clamps to zero. Preference persists in app settings. Failed prepare/start still uses existing rollback handling.

**DEV5 retained:** Play Playlist (button and D-pad RIGHT), shuffle, repeat Off/Playlist/Track and opt-in experimental double-NEXT headset seek. This candidate does not change the owner's neckband TAP=Volume Down and HOLD=Next mapping. Other older feature requests (inline move mode, one-key bookmarks, adjacent titles, PC bridge integration) remain open and are not claimed as implemented.

## Build and update for an owner-controlled trial

1. Extract this ZIP into the **existing GitHub Android build project**, preserving its workflow and signing identity. The ZIP is source, not an APK. Project root contains `settings.gradle` and `app/build.gradle`; intended Android SDK 33 / AGP 7.4.2 / Gradle 7.5 / JDK 17. This worker did not run an Android SDK build.
2. `applicationId` stays **`org.roarin.kyocerakeypad.sandboxwqa365`**, `versionCode` is **9**, and `versionName` is `0.2.0-dev6-wqb428-sleep-rewind-source`. This is intended as an update to the same DEV4/DEV5 disposable sandbox. Before installation, inspect package ID, versionCode and signing certificate. A signing mismatch should be investigated without uninstalling or clearing the existing app/data.
3. Test with backed-up/disposable music and audiobook. First verify existing playlist Play/Shuffle/Repeat and flip-closed playback; then timer 10m in Music and Audiobook (or shorter custom), cancel/reset, pause/save at expiration with flip shut, and audiobook Resume Off/5/10 at saved positions near 3s and 15s. Report actual UI/audio observations; a passing Linux test does not prove phone behavior.

## Tests and evidence

Run `bash tests/run_dev6_feature_smoke.sh` for Android-free Java policy and inherited DEV5 tests plus 20 adapted playlist-wiring and 20 new timer/rewind wiring checks. The DEV5 original static test still asserts `versionCode 8` and therefore fails as a historical assertion after this intentional version bump; its source is retained unchanged. `tests/test_dev6_playlist_compat.py` is the explicit v9 adaptation. `tests/SleepTimerPolicyTests.java` checks presets, custom integer validation, deadline math and Off/5/10 clamp behavior. No actual audio, Android UI compile, battery/sleep or signing tests were performed.

## Provenance and limitations

Source parent: `KYOCERA_KEYPAD_DEV5_WQB427_PLAYLIST_FEATURE_SOURCE_v0.1.9.zip`, SHA-256 `0124804c6e22554a8aa2195ff6664f623a7fea3a9977125e6fe6960367910f0a`.

The former DEV5 README and manifest are retained as `README_DEV5_HISTORICAL.md` and `SOURCE_MANIFEST_DEV5_HISTORICAL.json`; older historical sources and tests are preserved. The current `SOURCE_MANIFEST.json` is generated from the new candidate's exact bytes, excluding itself and transient `.build` files. Do not treat Linux synthetic test success as owner acceptance or an installed APK.
