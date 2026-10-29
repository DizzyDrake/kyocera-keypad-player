#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p .build
javac -Xlint:-options --release 8 -d .build app/src/main/java/org/roarin/kyocerakeypad/core/*.java tests/StateTests.java tests/PlaybackGateTests.java tests/AudioFocusGateTests.java tests/SnapshotExportTests.java tests/CompletionPolicyTests.java tests/RollbackProgressTests.java
java -cp .build RollbackProgressTests
java -cp .build StateTests
java -cp .build PlaybackGateTests
java -cp .build AudioFocusGateTests
java -cp .build SnapshotExportTests
java -cp .build CompletionPolicyTests
python3 tests/check_android_source_guard.py
python3 tests/check_audio_focus_integration.py
python3 tests/check_completion_policy.py
python3 tests/check_integrated_callback_guards.py
javac -Xlint:-options --release 8 -d .build app/src/main/java/org/roarin/kyocerakeypad/core/AlphabetJump.java tests/AlphabetJumpTests.java
java -cp .build AlphabetJumpTests
python3 tests/check_alphabet_ui.py
python3 tests/test_keypad_prompt_contract.py app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java
python3 tests/check_wqd059_ui_preview.py
# WQA355 transactional playlist/bookmark mutation and WQE082 failed-open peer review.
javac -Xlint:-options --release 8 -d .build app/src/main/java/org/roarin/kyocerakeypad/core/*.java tests/MutationCommitTests.java
java -cp .build MutationCommitTests
python3 tests/test_wqa355_mutation_wiring.py
python3 tests/test_wqe082_failed_open.py

# WQA357: current-state playlist completion resolution.
javac -Xlint:-options --release 8 -d .build app/src/main/java/org/roarin/kyocerakeypad/core/*.java tests/CompletionSelectionTests.java
java -cp .build CompletionSelectionTests
python3 tests/test_wqa357_completion_wiring.py

# WQA359 optional guarded pre-prepare rollback on current committed state.
javac -Xlint:-options --release 8 -d .build app/src/main/java/org/roarin/kyocerakeypad/core/*.java tests/FailedOpenRollbackTests.java
java -cp .build FailedOpenRollbackTests
python3 tests/test_wqa359_activity_rollback.py

# WQA365 disposable side-by-side package identity source preflight.
python3 tests/test_wqa365_sandbox_identity.py
