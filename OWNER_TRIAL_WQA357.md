# Keypad Player v0.1.7 — owner co-development and review

**Source only, not an APK or installed update.** Frozen parent is WQA355
v0.1.6 SHA-256 `a42ffda0b7798c6a779c03fbd0e6263e229f168a8400b6fa4ac5bb98e2beb2b5`.
Owner-installed v0.1.4, its app data and real playlists remain untouched.

The v0.1.7-source-review candidate preserves v0.1.6's durable playlist and
bookmark edits, failed-media-open rollback, preview, A–Z keypad navigation,
provisional dusty-red UI and source-only About metadata. It additionally
prevents a completion callback from choosing a track from a stale playlist
after successful reorder/remove/delete edits. It stops safely when the
completed track or playlist no longer belongs to the current playback context.

The offline pure-Java host tests are not an Android SDK build, E4831 audio
trial, call-pause proof, or a guarantee of on-device AtomicFile behavior.
The next owner-controlled step, after independent code review, is an exact
source-pinned Android build with recorded APK hash/signature and a safe rollback
plan. Test only with disposable media and playlists, including reorder while
playing, remove current/next entry, delete current playlist, incoming call
ringing/active-call pause, and manual resume. Do not install over v0.1.4 or
migrate real app data as a shortcut.

No additional Android permissions were introduced. The versionName is
`0.1.7-source-review`, versionCode 6, and the About dialog remains explicitly
unreleased. This document is not installation authorization.
