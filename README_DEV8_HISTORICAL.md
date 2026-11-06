# Kyocera Keypad Player DEV8 v0.2.2 — WQB430 source candidate

**Source-only. No Android SDK APK compilation, signing, installation, real E4831 keypad trial, or Bluetooth/audio proof.** This extends the B-owned DEV7 v0.2.1 source, keeping the earlier source ZIP and the owner's physically tested DEV4 v0.1.8 fallback unchanged. This is an experimental candidate, not a released app.

## New: playlist Move Mode without repeated action menus

In a playlist, highlight the track and press `*` to pick it up. Alternatively select a track and choose **Move in playlist (keypad Move Mode)** from its actions. The playlist stays visible with the selected track marked `> MOVING`, and the selection follows that track when it changes position. On this screen:

- **D-pad Up/Down** moves the selected track one row at a time, including held-key repeats; the surrounding list scrolls to keep it visible.
- **1 = move to top**, **9 = move to bottom**. These keys are active only in Move Mode, so Now Playing's 1/9 shortcuts are unchanged.
- **Center/Enter = save** the staged order once. **CLR/Back = cancel** without writing anything. The visible footer explains the controls. An unchanged order also exits without writing.

The draft is an in-memory ordered list keyed by the existing track identity, not the displayed title. Reordering does **not** move, rename or delete audio files, change a playing track, seek playback or change saved position. It uses the existing `StateMutation.prepareAndSave` and AtomicFile service writer for a single durable commit; failed writes retain the previously saved order. If the playlist entry list changed while the draft was open, saving is refused rather than overwriting the newer list. A cancelled or interrupted activity loses the *draft only*. For a non-shuffled active playlist, the service refreshes the current session's next/previous order after successful save without restarting audio; an already shuffled session keeps its current random sequence.

**Key assignments are provisional** until observed on the physical E4831. `*`/CLR may be delivered differently by the device. The `> MOVING` indicator, font size and long-playlist scrolling need owner observation. The UI does not offer a touch-oriented drag gesture; this is deliberately keypad-first.

## Retained from DEV7/DEV6/DEV5

- DEV7 Now Playing: 1/3 ±10s seek, 4/6 previous/next, 5 play/pause, adjacent titles and elapsed/duration. Audiobook 0 quick bookmark, 7/9 timestamp jump, # bookmark management.
- DEV6 Music/Audiobook sleep timer Off/10/15/30/60/custom, and optional audiobook resume rewind Off/5/10 seconds.
- DEV5 Play Playlist, Shuffle, Repeat Off/Playlist/Track, and experimental headset double-NEXT; existing app-private playlists, positions, audio focus and foreground service remain.
- No new 10-bookmark hard cap, import, media deletion or PC Playlist Desk integration. No autoplay on app launch.

## Owner-controlled build and bounded trial

1. Build the source in the owner's existing GitHub Android workflow, **without replacing or uninstalling DEV4** to resolve signing conflicts. The sandbox app ID remains `org.roarin.kyocerakeypad.sandboxwqa365`; `versionCode` is **11**, `versionName` is `0.2.2-dev8-wqb430-playlist-move-source`. Confirm signing certificate matches the installed sandbox before any in-place update; preserve app data and use disposable music.
2. In a disposable playlist of at least six nonalphabetical tracks, highlight the third track, press `*`, move up/down several times, then 1/9, then CLR; confirm original order remains. Repeat and save with Center, reopen playlist, verify order and the moved track remains highlighted. Try a second playlist with duplicate *titles* (distinct files/keys).
3. Repeat while playback is paused. Check Next follows the saved order with Shuffle off, and confirm playback progress and audio files were not changed. Report actual keys and on-screen behavior; do not assume the source test proves E4831 key delivery.

## Offline checks and provenance

Run `sh tests/run_dev8_feature_smoke.sh` for Android-free Java core tests, 32+ staged-order assertions, inherited DEV7/DEV6/DEV5 wiring checks adapted only for DEV8 version metadata, and new Move Mode source checks. Historical DEV7 test scripts remain preserved; they expect versionCode 10 and will intentionally fail their version-only assertions against DEV8. The new tests do not compile Android Activity/Service types or prove physical keypad, audio, lifecycle or signing.

Parent ZIP: `KYOCERA_KEYPAD_DEV7_WQB429_NOW_PLAYING_SOURCE_v0.2.1.zip`, SHA-256 `bd34377509205d72531df13590caa1a10ce756a4662d2ad9f4034d2b23624f48`.

The previous DEV7 README and manifest are preserved as `README_DEV7_HISTORICAL.md` and `SOURCE_MANIFEST_DEV7_HISTORICAL.json`. `SOURCE_MANIFEST.json` hashes packaged files except itself and transient build output. This package contains source only, not an APK.
