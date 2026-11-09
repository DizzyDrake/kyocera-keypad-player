#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
sh tests/run_bluetooth_probe_smoke.sh
mkdir -p .build
javac --release 8 -cp .build -d .build app/src/main/java/org/roarin/kyocerakeypad/core/VolumeDoubleTapSeek.java tests/VolumeDoubleTapSeekTests.java
java -cp .build VolumeDoubleTapSeekTests
python3 tests/test_bluetooth_double_volume_source.py

# DEV13 rescan/cleanup and read-only filtered snapshot regression.
javac --release 8 -cp .build -d .build \
  app/src/main/java/org/roarin/kyocerakeypad/core/PlayerState.java \
  app/src/main/java/org/roarin/kyocerakeypad/core/StateCodec.java \
  app/src/main/java/org/roarin/kyocerakeypad/core/PhoneSnapshotExport.java \
  app/src/main/java/org/roarin/kyocerakeypad/core/LibraryAvailability.java \
  tests/LibraryAvailabilityTests.java
java -cp .build LibraryAvailabilityTests
python3 tests/test_library_availability_source.py
