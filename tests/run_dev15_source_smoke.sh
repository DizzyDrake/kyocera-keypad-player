#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Source-only verification. Android SDK build, real device, and SMS are NOT tested.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build-dev15
javac -Xlint:-options --release 8 -d .build-dev15 app/src/main/java/org/roarin/kyocerakeypad/core/*.java tests/*Tests.java
for src in tests/*Tests.java; do
  class="$(basename "$src" .java)"
  java -cp .build-dev15 "$class"
done
for test in \
  tests/test_dev15_interrupted_notification.py \
  tests/test_dev14_active_playlist_source.py \
  tests/test_dev13_integration_source.py \
  tests/test_bluetooth_double_volume_source.py \
  tests/test_bluetooth_probe_source.py \
  tests/test_library_availability_source.py \
  tests/test_stale_import_source.py
  do python3 "$test"; done
printf 'PASS: DEV15 selected behavior + source contracts; NOT Android compile or handset SMS test\n'
