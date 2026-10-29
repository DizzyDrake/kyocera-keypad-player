#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p .build
javac -Xlint:-options --release 8 -d .build app/src/main/java/org/roarin/kyocerakeypad/core/*.java tests/*Tests.java
for c in RollbackProgressTests StateTests PlaybackGateTests AudioFocusGateTests SnapshotExportTests CompletionPolicyTests AlphabetJumpTests MutationCommitTests CompletionSelectionTests FailedOpenRollbackTests FailedOpenSelectionTests MediaTransportSequencerTests; do
  java -cp .build "$c"
done
python3 tests/test_wqb405_service_wiring.py
