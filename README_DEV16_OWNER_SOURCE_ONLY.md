# Dumbplayer DEV16 — independent remote Next/Previous seek switches

**Source-only candidate, November 11, 2026.** Neither an APK nor an installed device update. Preserve Aurora's working application, its signing key, audio, playlists and progress. No code from Podcast Addict copied.

## Direct owner decisions

Aurora confirmed long press **+ = Next**, long press **− = Previous**, delivered to Dumbplayer with the Kyocera flip closed. She requests that these remote media commands **seek within audiobooks by +30/−15 seconds by default**, and that the seek-versus-change-track behavior be **easy to switch ON/OFF independently for music and audiobooks**.

## Candidate behavior

- Audiobook remote Next/Previous defaults to seek +30/−15 seconds (ON).
- Music remote Next/Previous defaults to ordinary next/previous tracks (OFF).
- Both independent switches are at **Listening settings**; a one-press toggle for the currently active type is also on **Now Playing**. Each value persists separately in `playlist_playback_options_v1` (`remote_seek_book`, `remote_seek_music`). Absent old keys default to the owner-selected values.
- MediaSession next/previous callbacks, Bluetooth media key processing, and notification Previous/Next buttons use the same mapping. Their notification labels reflect current behavior.
- **Local keypad [4]/[6] still navigates tracks** regardless of the headset switch. Local [1]/[3] 10-second seeks, headset short-press volume, the separate music/audiobook shuffle preferences, DEV15 paused notification, the app-private playlists and file identities remain unchanged. No audio file deletion, automatic resume, or network requests.
- With seek enabled but no prepared player, a remote skip is a no-op, avoiding an accidental jump into a different book.
- Debug-only experimental volume-index polling remains disabled in ordinary release builds.

## How to integrate (source only)

Apply changed files over the existing Dumbplayer GitHub source after the preserved **DEV13 R2 full**, **DEV13 R3 changed-files**, **DEV14 R1 changed-files**, and **DEV15 R1 changed-files** overlays, in that order. The ZIP includes a full-tree `SOURCE_MANIFEST.json`, a DEV16 manual unsigned build workflow, edited app/source/test files and this README. Never apply it over a different project or a signed APK.

The workflow is `dev16-unsigned-local-sign.yml`: manual trigger only. Any assembled release artifact is **unsigned**, must be verified and signed locally with the owner-established permanent key and checked for compatible package identity before an in-place update. No keys, passwords or APK included.

## Evidence and limits

`tests/run_dev16_source_smoke.sh` runs the new 16-combination pure-Java policy tests, 22 source-wiring checks, and inherited regression suites; results in `DEV16_TEST_LOG.txt`. The inherited version-literal test fixtures were updated only in this DEV16 candidate and old originals remain frozen. Android Java syntax parsing and fresh 4-layer ZIP reconstruction/hash verification are separate offline checks; **neither is an Android Gradle compile nor an on-device test**. Future physical checks: both directions on the closed flip, both playlist types and toggle persistence, paused/playing notification buttons, D-pad independent track navigation, and no unexpected volume adjustments.

This patch does not claim reproducing Podcast Addict internals; it emulates the user-visible standard-media-command remapping.
