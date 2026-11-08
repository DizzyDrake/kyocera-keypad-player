#!/bin/sh
# Runs only Android-free Java behavior and source wiring; NOT an APK compile.
set -eu
cd "$(dirname "$0")/.."
mkdir -p .build
javac --release 8 -d .build app/src/main/java/org/roarin/kyocerakeypad/core/*.java tests/*Tests.java
for c in RollbackProgressTests StateTests PlaybackGateTests AudioFocusGateTests SnapshotExportTests CompletionPolicyTests AlphabetJumpTests MutationCommitTests CompletionSelectionTests FailedOpenRollbackTests FailedOpenSelectionTests MediaTransportSequencerTests PlaylistPlaybackOrderTests; do
 java -cp .build "$c"
done
python3 tests/test_dev6_playlist_compat.py

java -cp .build SleepTimerPolicyTests
python3 tests/test_dev6_wiring.py
