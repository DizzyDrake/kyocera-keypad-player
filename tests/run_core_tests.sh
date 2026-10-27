#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p .build
javac -Xlint:-options --release 8 -d .build app/src/main/java/org/roarin/kyocerakeypad/core/*.java tests/StateTests.java tests/PlaybackGateTests.java tests/AudioFocusGateTests.java tests/SnapshotExportTests.java tests/CompletionPolicyTests.java
java -cp .build StateTests
java -cp .build PlaybackGateTests
java -cp .build AudioFocusGateTests
java -cp .build SnapshotExportTests
java -cp .build CompletionPolicyTests
python3 tests/check_android_source_guard.py
python3 tests/check_audio_focus_integration.py
python3 tests/check_completion_policy.py
python3 tests/check_integrated_callback_guards.py
