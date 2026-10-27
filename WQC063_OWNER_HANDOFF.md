# Kyocera Keypad Player v0.1.4 — owner-controlled next step

**Source only, not an APK.** The candidate combines the prior v0.1.3 audio-focus pause with the reviewed D018 and C045 callback guards. No Android SDK build, E4831 device test, phone call, or owner installation occurred.

For future joint review, inspect the Activity completion/error/prepared listeners and `stopPlayer()` cleanup, then build in an owner-controlled Android environment only with fresh permission. On a disposable/test playlist, verify incoming ringing and active calls pause music and audiobooks without advancing, that the same track/playlist/timestamp survives, that manual Play works after the call, and that Back/Home navigation does not reopen Now Playing. Do not use irreplaceable media or real messages for initial tests.

`tests/run_core_tests.sh` exercises pure Java and static checks on Linux; it does not compile the Android Activity. No background audio service is implemented. Do not claim that this candidate pauses playback during calls on actual hardware until owner-observed phone testing. The conservative after-call manual Play policy remains a proposal, not an owner-confirmed decision.

Frozen parent WQE019 v0.1.3 SHA-256: `31c47aaf56d49df8ca16759095159df4ff8df8635f7a01c8963aa8447a16a0f3`. Prior optional patches WQD018 and WQC045 remain separately preserved. No migration of live media or installed source.
