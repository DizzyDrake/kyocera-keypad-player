# Keypad Player v0.1.6 — owner collaboration / build boundary

This ZIP is a **source-only candidate**, not an APK. The owner-installed v0.1.4
is preserved. Do not overwrite the existing app or its saved playlists to test
this candidate. The WQD059 v0.1.5 parent is also preserved unchanged.

## What is new

- Explicit preview, D-pad A–Z, larger dusty-red controls and About metadata
  inherited from WQD059 v0.1.5.
- An unstarted new media selection is restored when media opening fails,
  integrating WQE082's optional review patch once.
- Nine playlist/bookmark edits commit to `AtomicFile` before the in-memory
  state is published. A failed write retains the prior state, rather than
  allowing a later unrelated save to commit an earlier failed edit.

## Next owner-controlled steps (not performed by worker)

1. Choose an Android build method (e.g., the owner's existing GitHub Actions
   workflow with JDK 17 and Android SDK) and inspect this source. Confirm
   source ZIP SHA-256 and record the resulting APK SHA-256, versionCode 5,
   signature and rollback route. No worker has compiled an Android APK.
2. Only after choosing a safe separate/disposable trial environment, check
   physical E4831 keypad focus, A–Z navigation, preview Stop/Back, and both
   music/audiobook listening positions using **disposable** test media.
3. Check an intentionally missing disposable media entry and, if practical,
   a controlled storage-write failure; verify both the displayed warning and
   subsequent persisted state. Separately test ringing/in-call pause; source
   audio-focus guards do not prove hardware behavior.

No live app, private music, phone, F:, GitHub, credentials or schedules were
accessed. The build's `BUILD_UTC` is Gradle configuration time, not verified
APK compilation completion. `Release date: Not released` remains truthful.
