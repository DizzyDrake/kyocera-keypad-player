# Keypad Player DEV5 v0.1.9 — WQB427 feature source candidate

**Status:** Extracted Android project SOURCE ZIP. NOT an APK, not compiled against Android SDK in this worker, not installed, not owner-tested. This is a feature-first extension of the **owner-tested DEV4 v0.1.8** baseline. DEV4's flip-closed playback, Bluetooth Play/Pause, Volume Up/Down and hold-to-Next were reported working by the owner on October 29, 2026; DEV5's changes have NOT been physically verified.

## What's new

- **Play Playlist** at top of a playlist's detail view, plus physical **D-pad RIGHT** from the selected playlist in the Playlists list or while viewing its detail. No autoplay on app launch or reconnect.
- **Shuffle ON/OFF** in playlist detail and Now Playing. OFF starts Play Playlist at saved first entry. ON starts at a random track and shuffles the rest. Toggling while playing retains the current track and rebuilds the remaining order. Saved playlist order is never rewritten.
- **Repeat Off / Repeat Playlist / Repeat Track** via a cycling control in playlist detail and Now Playing. Off stops at end; Playlist wraps; Track repeats on natural completion. Manual NEXT is not captured by Repeat Track. Options persist in app preferences, not in the old state codec.
- **Optional headset experiment** in Help: Double NEXT media event within 350ms seeks +10 seconds. OFF by default. Enabling delays a single NEXT by 350ms; a genuine **tap on owner's neckband is Volume Down, HOLD is Next**. Two volume-down taps may never arrive as two NEXT events; this is not proven to work on the headset. Working volume keys are not remapped.

## Owner GitHub build path (do not uninstall)

1. Use the **same GitHub repo/workflow and signing identity** that produced the owner's installed DEV4 v0.1.8 sandbox. Extract this ZIP into the repository root so `app/build.gradle` and `settings.gradle` are at their expected paths. Uploading the ZIP alone does not build it. Preserve the working `.github/workflows/` and signing configuration; this package deliberately does not ship a replacement workflow or keystore.
2. The source retains `applicationId org.roarin.kyocerakeypad.sandboxwqa365`, increments `versionCode` from **7 to 8**, and uses `versionName 0.1.9-dev5-wqb427-playlist-source`. The intended toolchain is Android SDK 33, AGP 7.4.2, Gradle 7.5 and JDK 17. **No SDK build was performed here.** A GitHub build may report compile errors; preserve the log and source state if it does.
3. Before any install, confirm the APK package is exactly `org.roarin.kyocerakeypad.sandboxwqa365`, versionCode **8**, and that its signing certificate matches the installed sandbox. A mismatch may prevent in-place update. **Do not uninstall, clear storage, or install as a new app** to resolve a signature mismatch; preserve playlists/bookmarks/progress and the original player.
4. On a deliberate owner trial, use backed-up/disposable music first. Test Play Playlist with Shuffle OFF, then Shuffle ON, Repeat Off/Playlist/Track, D-pad RIGHT, and only then optional double NEXT if desired. Record actual on-screen and headset behavior. Incoming-call pause and physical double tap remain unproven.

## Tests and limits

`bash tests/run_dev5_feature_smoke.sh` runs Android-free pure-Java state/transport tests and 20 static wiring checks. The new queue policy adds 23 Java assertions. All passed in the worker's Linux JDK 21 with `--release 8`. The inherited WQB405 script's single literal `CompletionPolicy.nextSelection(...)` source assertion is now obsolete because DEV5 replaces that selection with current-state guarded shuffled/repeat order. **Not an Android compilation, emulator run, audio test, phone test, signing check or guarantee of safe in-place update.**

The old DEV4 README, original manifests and owner-trial provenance remain as explicitly named HISTORICAL files. This source ZIP does not overwrite any original project source or owner data. The current owner instruction prioritizes a functional prototype and feedback over repeated speculative defect hunts.
