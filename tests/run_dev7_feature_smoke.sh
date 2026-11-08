#!/bin/sh
# Android-free Java behavior and source wiring only; no APK compilation.
set -eu
cd "$(dirname "$0")/.."
mkdir -p .build
javac --release 8 -d .build app/src/main/java/org/roarin/kyocerakeypad/core/*.java tests/*Tests.java
for c in RollbackProgressTests StateTests PlaybackGateTests AudioFocusGateTests SnapshotExportTests CompletionPolicyTests AlphabetJumpTests MutationCommitTests CompletionSelectionTests FailedOpenRollbackTests FailedOpenSelectionTests MediaTransportSequencerTests PlaylistPlaybackOrderTests SleepTimerPolicyTests NowPlayingNavigationTests; do
 java -cp .build "$c"
done
python3 tests/test_dev7_playlist_compat.py
python3 tests/test_dev7_sleep_wiring.py
python3 tests/test_dev7_wiring.py
