#!/bin/sh
# Source-only feature checks. Android SDK/phone build NOT performed.
set -eu
cd "$(dirname "$0")/.."
mkdir -p .build
javac -Xlint:-options --release 8 -d .build app/src/main/java/org/roarin/kyocerakeypad/core/*.java tests/*Tests.java
for c in RollbackProgressTests StateTests PlaybackGateTests AudioFocusGateTests SnapshotExportTests CompletionPolicyTests AlphabetJumpTests MutationCommitTests CompletionSelectionTests FailedOpenRollbackTests FailedOpenSelectionTests MediaTransportSequencerTests PlaylistPlaybackOrderTests SleepTimerPolicyTests NowPlayingNavigationTests PlaylistReorderDraftTests; do
 java -cp .build "$c"
done
python3 tests/test_dev8_playlist_compat.py
python3 tests/test_dev8_sleep_wiring.py
python3 tests/test_dev8_now_wiring.py
python3 tests/test_dev8_move_wiring.py
