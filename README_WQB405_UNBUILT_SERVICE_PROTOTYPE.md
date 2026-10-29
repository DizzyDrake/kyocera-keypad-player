# WQB405 — Kyocera Android 10 background playback integration prototype (SOURCE ONLY)

**Task:** `WQ-20261028-028` · **Worker:** B · **Date:** 2026-10-28 America/Chicago.

## Source identity and non-release status

This is an **uncompiled, uninstalled, unaccepted engineering prototype**, not a buildable APK guarantee, production update, owner-tested release or replacement for either existing installation. The source patch applies to the frozen WQA365 v0.1.7 sandbox ZIP with SHA-256 `5537a2ff7a8c539b2d33b71a8e576d215f7b54d0d0ef5353ce548b250dc955ba`. It deliberately changes the sandbox application ID to `org.roarin.kyocerakeypad.sandboxwqb405` to avoid overwriting the original app or the owner's installed WQA365 sandbox if a future supervised build is attempted. No build or installation was performed here.

## Actual code changes (not device evidence)

- Introduces `KeypadPlaybackService` as the single in-process owner of `MediaPlayer`, `PlayerState`, the AtomicFile state snapshot, focus gates, progress saving and playlist completion. Activity binds to that shared service and edits/publishes the same state; no second Activity-owned snapshot is loaded.
- Moves prepared/completion/failure/rollback callbacks into the Service. The service keeps a 5-second position-persistence tick independently of the Activity. The Activity no longer pauses normal playback on `onPause` or releases the normal player on `onDestroy`; its preview audition still stops when the Activity pauses.
- Preserves **explicit** Home/Back-from-Now-Playing pause, focus-loss pause with no automatic restart on focus gain, explicit Resume and separate music/audiobook progress. MediaSession and foreground notification provide basic Play/Pause, Next and Previous commands. Reuses WQB403's 31-check Java media transport sequencer for standard media keys; experimental double-press seeking remains **disabled** pending actual headset event traces.
- Declares a non-exported `mediaPlayback` foreground service, `FOREGROUND_SERVICE` permission and Android 10-targeted source. Adds a distinct prototype app label/ID, rather than changing the installed app's identity.

## Checks performed and what they mean

- Frozen source ZIP SHA-256 verified; original ZIP had 50 entries and was used as the patch baseline.
- 12 pure Java test classes passed **336** assertions across existing state, focus, playback, rollback, completion, mutation, snapshot and WQB403 media transport logic. These test Android-free components only.
- 25/25 **static source wiring** checks passed for service ownership, manifest, foreground start, explicit Home pause, focus-loss handling, MediaSession callbacks, state persistence and sandbox identity. These checks inspect source text, not compiled Android behavior.
- The original `tests/run_core_tests.sh` was run and **failed** at the first legacy Activity-specific static guard (expected after moving the playback gate from Activity into Service). Its original source-string assertions are not equivalent to Android runtime tests. The original test scripts were preserved unchanged; the new `tests/run_wqb405_offline.sh` runs the pure Java tests and new architecture checks. See saved logs and test manifest.
- Patch replay against the exact frozen ZIP is required before an integrator considers this a source candidate. Passing replay proves only that the patch applies and reproduces files, not that Android compilation succeeds.

## Known gaps / must-fix-before-APK

1. **No Android SDK / `android.jar` / Gradle executable was available in this worker container.** No Android compilation, lint, APK, manifest merge, emulator or physical E4831 test occurred. Java API signatures and Android lifecycle interactions remain unverified. The patch must be reviewed, compiled and corrected with an Android 10 toolchain before any owner-supervised disposable APK trial.
2. **Call and audio-focus tests are open.** A real incoming call must pause, preserve position and not auto-resume; ringing-only and call-answer behavior need distinct owner observation. Headset button events, notification actions, flip-close, screen sleep, Activity recreation, battery restrictions and media-session routing need physical tests.
3. **Service lifetime and durability need review.** Confirm process-kill/restart does not autoplay, no stale callbacks alter the wrong session, no background save races with a playlist mutation, and no foreground notification persists incorrectly after explicit Stop. The current Service uses `START_NOT_STICKY` and deliberately does not auto-restart playback.
4. **P2/P3 owner wishes are not integrated**: prominent Resume Last, compact keypad legends, visible reorder shortcuts, elapsed/total/progress, fast bookmark names/count, Add-before-Preview, music/audiobook sleep timer (10/15/30/60/custom) and optional audiobook resume rewind (Off/5/10). Do not call these complete.
5. **Wishtonwish/Windows playlist sync is separate**: owner-tested metadata export does not establish ADB round-trip/import. Preserve canonical metadata and real playlists; no real media or phone data was used here.
6. **Inherited Activity-specific static guards need migration**, not silent removal. Rewrite only after checking the actual new Service behavior and Android compile. Keep their original failure log for provenance.

## Reproduction in an isolated source copy

Extract the exact WQA365 frozen source ZIP into an empty scratch directory. Apply `WQB405_ANDROID10_SERVICE_INTEGRATION_UNBUILT.patch` with `patch -p1`, then run `bash tests/run_wqb405_offline.sh` using Java 8-compatible `javac` and Python 3. Do **not** use this patch to overwrite the owner's original app, WQA365 sandbox source, Android installation or project canonical history. This source prototype requires an independent SDK-backed review before any APK is prepared.
