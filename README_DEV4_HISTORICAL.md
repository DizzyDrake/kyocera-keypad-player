> **WQA365 disposable sandbox source variant.** This is NOT an update to the installed Keypad Player. Read `README_WQA365_DISPOSABLE_SIDE_BY_SIDE_TRIAL.md` before building or considering installation.

# Keypad Player v0.1.5 — WQD059 integrated OFFLINE source review candidate

**Source only. No APK built, no Android SDK compilation, no owner-device test, no installation or release.**

Frozen WQC063 v0.1.4 parent SHA-256 `8f3dec513ed7b1205a7a0e8275fe4c7ec29988cd030f9deeba5526d4ee0e1623`. D058 reviewed patch combination: WQD049 + WQA339 + WQC070 applied with `patch -p1 --fuzz=0`; WQE076's exact tested prompt body and EditorInfo import transplanted after verifying against frozen parent. WQE077 is intentionally **not** reapplied because WQD049 already includes its completion authorization-before-save ordering.

## Proposed owner-visible changes

- Browse/search library selection now offers explicit **Preview / Play** before playlist insertion. Preview uses a separate `MediaPlayer`, requires explicit Center/Play, pauses/stops on focus loss or navigation, and never selects music/audiobook listening progress, creates bookmarks, or changes playlist order. Previous normal player is stopped only after saving its position; a failed persist blocks preview. The actual Android media lifecycle and E4831 keypad require testing.
- Explicit **Add to selected playlist** or **Choose playlist to add** actions. A failed `AtomicFile` save rolls back the just-added in-memory entry to prevent an accidental later commit. Missing/changed audio identities cannot be added through the new flow. Existing playlist editing remains.
- D-pad Right A–Z title index and keypad Save/Cancel/IME Done path from reviewed optional patches. E4831 physical behavior remains unverified.
- Provisional dusty-red/burgundy header (`#713E46`), off-white body, dark text, visible light focus highlight, 18sp multiline list rows and 15sp footer. These colors are a reversible **proposal**, not owner-selected swatches. Actual E4831 layout/clipping remains untested.
- Keypad-accessible About dialog: version, **Gradle configuration UTC** generated on the builder machine (not an independently verified APK build completion timestamp), source preparation date, `Release date: Not released`, and owner-requested attribution `Made by GPT-6 and Aurora Williamsen`. No fictional release date or APK build date is hardcoded.

## Host-only tests

Run `sh tests/run_core_tests.sh` from extracted source with JDK 8+ and Python 3. This runs inherited pure-Java and source checks, WQC070 alphabet tests, WQE076 keypad prompt source checks, and new WQD059 source checks. The WQC070 original test's old inline-add expectation is replaced in this candidate by a stronger explicit-add-helper/rollback check; the original failing output is preserved in queue evidence, not concealed. No Android SDK is present in this worker environment; host/static PASS is not proof the Activity compiles, that Gradle metadata generates, or that playback/keypad works on the E4831.

## Owner-review / trial boundaries

Do not install over the owner-tested v0.1.4 until Aurora reviews this candidate and approves a build and disposable-media phone trial. On-device first trial: create a disposable playlist with physical keys, Right → A–Z → Center → CLR, audition a search result without adding, confirm saved music/audiobook positions unchanged, then explicitly add a track. Call-pause, saved-state crash recovery, build metadata and actual screen contrast need separate validation. No background playback service exists. No permissions beyond the existing READ_EXTERNAL_STORAGE were added.

No owner media, real export JSON, F:, live phone, credentials, GitHub, Docker, or schedules were accessed.

## WQA355 v0.1.6 source-only durability integration (2026-10-27)

This is an **offline source candidate**, not an APK or owner-installed update. It
builds on the exact frozen WQD059 v0.1.5 source and integrates WQE082's reviewed
failed-media-open selection restoration once. Nine playlist/bookmark mutation
paths now edit a decoded copy of the PlayerState and publish it in memory only
after a successful AtomicFile write. A failed write or edit leaves the original
in-memory state unchanged; playlist deletion first requires a successful
previous-playhead save. The existing guarded add-track path is retained.

`bash tests/run_core_tests.sh` runs the inherited host suite and the new
fictional pure-Java 84-assertion mutation test, five Android-source wiring tests,
and seven WQE082 regression checks. These are **not** an Android compilation,
real AtomicFile injection, actual media playback, keypad test, or call-pause
validation. The source ZIP includes no Gradle wrapper, SDK or built APK.

**Known limitations:** Other state writes (seek/playhead, library scan and
completion) are outside the new transactional edit helper. A failed media-open
restoration write can still leave the persisted new selection; it displays a
warning. Saving a name in a dialog that encounters a storage failure may close
the dialog and require retyping. Owner-installed v0.1.4 remains unchanged.
See `OWNER_TRIAL_WQA355.md` for the bounded owner collaboration and rollback.


## WQA357 v0.1.7 completion-context integration (2026-10-27)

**Offline source review candidate only; no Android build/APK or E4831 device test.**
This follows independent WQD061 discovery that after a successful playlist
copy-persist-publish reorder/removal, the old completion listener mixed a
current-state next index with a captured old Playlist object. The callback now
resolves the current playlist and index together via the pure-Java
`CompletionPolicy.nextSelection` helper, refusing to advance if the playlist,
completed track, listening kind, progress identity, or next track is missing.
The existing playback/focus authorization guard remains ahead of this lookup.

The new `CompletionSelectionTests.java` executes the actual PlayerState and
CompletionPolicy with fictional music/book entries. Its 21 assertions include
reorder, removal, deletion, stale progress, missing media and kind separation.
`tests/test_wqa357_completion_wiring.py` checks Activity callback wiring.
The inherited host tests remain. The baseline stale selection failure is
recorded in the separate Work Queue evidence. No background playback, Android
MediaPlayer callback or incoming-call behavior was exercised here.

See `OWNER_TRIAL_WQA357.md` for source-only build/rollback boundaries.
