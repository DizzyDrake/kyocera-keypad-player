# Kyocera Keypad Player DEV7 v0.2.1 — WQB429 source candidate

**Source-only. No Android SDK APK compilation, no installation, no physical E4831 or Bluetooth testing.** This is a separate derivative of B-owned DEV6 v0.2.0. The owner-tested DEV4 v0.1.8 is the physical fallback; DEV5 and DEV6 parent ZIPs remain unchanged. This is an experimental build candidate, not a released app.

## New Now Playing behavior

- In **Music and Audiobook Now Playing**, phone number keys **1 = rewind 10s, 3 = forward 10s, 4 = previous playlist track, 6 = next playlist track, 5 = play/pause**. Visible rows and a compact footer repeat the map. Number-key handlers are scoped to the NOW screen, ignore repeated DOWN/UP events and do not run when an EditText is focused. They do not change Library D-pad A–Z or playlist navigation.
- Header shows **previous, current, next track titles** from the actual selected playlist and, when Shuffle is active, the service's existing session shuffle order. Repeat Playlist wraps titles; Repeat Track does not change the manual skip labels. If the shuffle order becomes stale after playlist edits, the display says unavailable instead of pretending the saved order predicts the next shuffled item. Missing boundaries show `—`. Header truncates long names on this small display; verify actual phone legibility.
- Now Playing footer shows **elapsed / full duration** (or `unknown`), sleep timer, and shortcuts. Elapsed position refreshes every 2 seconds without rebuilding the list. Service callback refreshes adjacent titles when the current track changes.
- In **Audiobook Now Playing only**, **0 = save a timestamp bookmark immediately**, **7 = jump to earlier bookmark**, **9 = jump to later bookmark**, **# = browse/edit bookmarks**. Jump order is by timestamp relative to current playhead, not creation order; it is restricted to the current track. The quick save auto-labels the timestamp, does not prompt or pause playback, and uses existing durable `commitMutation` path. Rename/Delete remain on the existing bookmark management page. There is no new hard ten-bookmark cap and no silent deletion.

These are **provisional key assignments** based on the owner's requested workflow, not evidence that the E4831 actually delivers every number or `#` event to this Activity. Hardware and text-entry conflict behavior must be observed on the phone before acceptance. Previous/next keys use the service's existing `skip()` path, not an independent playback engine.

## Retained DEV6 / DEV5 features

- DEV6: Music/Audiobook sleep timer Off, 10/15/30/60/custom, remaining time and service expiry pause/save; audiobook explicit-resume rewind Off/5/10 seconds. Process-death timer restoration remains intentionally absent, and flip-closed expiry is unverified.
- DEV5: Play Playlist, Shuffle, Repeat Off/Playlist/Track, optional double-NEXT headset experiment. The actual owner headset TAP = Volume Down and HOLD = Next. This candidate does not remap headset volume buttons.
- Prior: playlists and audiobook progress remain in the same sandbox app-private state. No media file deletion or playlist import/migration is added. **Inline playlist Move Mode and PC Playlist Desk integration remain separate unimplemented requests.**

## Owner-controlled GitHub build and trial

1. Extract this ZIP into the **existing owner GitHub Android build workflow**, preserving its signing identity. It contains source, not a compiled APK. Intended toolchain is Android SDK 33, AGP 7.4.2, JDK 17 and the Gradle version already configured in the owner's workflow; no toolchain was run here.
2. Confirm `applicationId` = `org.roarin.kyocerakeypad.sandboxwqa365`, `versionCode` = **10**, `versionName` = `0.2.1-dev7-wqb429-now-playing-source`. The package ID is unchanged from DEV4/DEV5/DEV6. Before an in-place install, check signing certificate matches the installed sandbox; **do not uninstall or clear app data** to work around a mismatch. Use disposable media and backup existing sandbox data first.
3. On the E4831, play a deliberately nonalphabetical 3-track playlist. Check number keys 1/3/4/5/6 and previous/current/next title labels, including boundaries, shuffle and repeat. In an audiobook, press 0 at two positions and try 7/9/#, then reopen to confirm bookmarks persisted. Also check the inherited DEV6 sleep timer and resume rewind. Record actual key actions and screen/audio results; don't infer success from these source tests.

## Offline tests and provenance

Run `sh tests/run_dev7_feature_smoke.sh`: Android-free Java core tests, 25 new navigation/bookmark assertions, 20 adapted DEV5 playlist checks, 20 adapted DEV6 timer/rewind checks, and 24 new DEV7 source-wiring checks. Java syntax parser separately checked all 15 application `.java` files without Android type resolution. These tests **do not** compile Android Activity/Service types, prove UI dimensions, media focus, hardware key delivery, signing, or device playback.

Parent: `KYOCERA_KEYPAD_DEV6_WQB428_SLEEP_REWIND_SOURCE_v0.2.0.zip` SHA-256 `76d8d4bd57a0fe8ac6655737ae4b6b6b237111b26ef8620fc463c616776232d3`.
Historical DEV6 README/manifest retained as `README_DEV6_HISTORICAL.md` / `SOURCE_MANIFEST_DEV6_HISTORICAL.json`. The current `SOURCE_MANIFEST.json` hashes all other packaged source files, excluding itself and transient build outputs. Original parent ZIP was not modified.
