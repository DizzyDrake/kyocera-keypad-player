# Kyocera E4831 Keypad Player v0.1.4 — consolidated audio-focus and callback safety source-only candidate

**WQ-E-20261024-019 · OFFLINE SOURCE ONLY · NOT AN APK · NOT COMPILED AGAINST ANDROID SDK · NOT INSTALLED OR PHONE-TESTED.**

Frozen parent: WQ147 v0.1.2 Android10 metadata-export source-only ZIP, SHA-256 `7ba462c7da7ccee8de57340a47a3cce68c2912df89d480742f1837305a54a87a`. The parent ZIP, WQ143/144/147 history, owner device and media are unchanged. This candidate retains WQ147's on-phone playlist/bookmark/player and manual metadata export behavior. It addresses Aurora's 2026-10-24 requirement to **pause actual playback** during an incoming call rather than merely mute it.

## Intended behavior in the uncompiled Activity

- Explicit Play requests Android 10 `AudioManager` focus with music or speech `AudioAttributes`. A denied request or `MODE_RINGTONE`, `MODE_IN_CALL`, `MODE_IN_COMMUNICATION` blocks starting playback. No telephony/SMS permissions.
- `AUDIOFOCUS_LOSS`, `AUDIOFOCUS_LOSS_TRANSIENT`, and `AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK` all revoke playback authorization and call `MediaPlayer.pause()` if prepared/playing. The app snapshots and persists the active music or audiobook position without resetting the other context.
- `AUDIOFOCUS_GAIN` never auto-resumes: after a call the user must select Play. This is a conservative **proposed** post-call policy, not a separately confirmed owner decision. The focus state machine and existing foreground gate both must permit `MediaPlayer.start()` in async prepare, seek-complete and manual Play paths.
- Focus is abandoned on manual Pause, navigation, stop, Activity pause/destroy. A generation counter ignores delayed focus callbacks belonging to abandoned requests. The existing app does **not** play in background: a future background playback Service must own this focus lifecycle before background audio can be claimed.
- Existing playlist order, separate music/audiobook positions, bookmarks, MediaStore validation, and manual metadata export remain unchanged in production source apart from the Activity and the new pure-Java focus gate.

## Tests performed

Run `sh tests/run_core_tests.sh` from the extracted source folder (JDK 8+, Python 3). On the worker's isolated host: 31 core state, 10 lifecycle gate, 18 audio-focus gate/fictional-state, 24 snapshot export assertions, 10 inherited updated static checks, and 16 new static checks all passed. The original WQ147 baseline also passed 31+10+24+9. The inherited static test initially failed because it matched the obsolete `playbackGate.canStart()` expression; that failure was preserved and the test strengthened to require the combined foreground+focus gate.

**These tests do not compile or run `KeypadPlayerActivity`**: no Android SDK/API29 `android.jar`, emulator, APK, incoming-call event, audio hardware, Bluetooth/headset, background service or E4831 was available. A focus-loss callback during ringing and its timing on the actual E4831 are **unverified**. Android 10 does not guarantee all apps honor audio focus. `AudioManager.getMode()` is a secondary conservative guard, not proof that every call state will be detected.

## Owner-controlled next step

Review the small source diff, then independently compile with a real Android API29 toolchain and test with fictional media on an emulator. Only with fresh Aurora approval: install a built APK on the E4831 and check ringing, answered/declined/outgoing calls, manual resume, bookmarks and playback position. Background playback remains unimplemented. Do not flash/install or modify existing media, call data, ADB settings, protected F:, or schedules on the basis of this source-only candidate.

## v0.1.4 source-only integration (WQ-C-20261026-015)

Combined reviewed WQD018 late-prepare navigation, stale MediaPlayer error, guaranteed release after reset failure, and WQC045 completion/focus authorization guards. This is not a new APK and is not phone-tested. The original WQE019 v0.1.3 remains immutable. No background audio service exists; no call interception or telephony permission is added. Remaining paused after a call until manual Play is a proposed conservative default, not a separately confirmed owner choice. A future owner-supervised Android build and actual ringing/active-call, position, playlist and keypad trial are necessary.
