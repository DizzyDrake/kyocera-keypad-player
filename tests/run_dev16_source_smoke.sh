#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Android-free source/pure-Java tests only. Not an SDK build.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build-dev16
javac --release 8 -d .build-dev16 app/src/main/java/org/roarin/kyocerakeypad/core/*.java tests/*Tests.java
for src in tests/*Tests.java;do java -cp .build-dev16 "$(basename "$src" .java)";done
for test in tests/test_dev16_remote_skip_source.py tests/test_dev15_interrupted_notification.py tests/test_dev14_active_playlist_source.py tests/test_dev13_integration_source.py tests/test_bluetooth_double_volume_source.py tests/test_bluetooth_probe_source.py tests/test_library_availability_source.py tests/test_stale_import_source.py;do python3 "$test";done
printf 'DEV16 host source checks passed; no Android SDK/device test\n'
