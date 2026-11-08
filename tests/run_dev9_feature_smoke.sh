#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
sh tests/run_dev8_feature_smoke.sh
mkdir -p .build
javac -Xlint:-options --release 8 -cp .build -d .build app/src/main/java/org/roarin/kyocerakeypad/core/HomeMenuOrder.java tests/HomeMenuOrderTests.java
java -cp .build HomeMenuOrderTests
python3 tests/test_dev9_home_wiring.py
