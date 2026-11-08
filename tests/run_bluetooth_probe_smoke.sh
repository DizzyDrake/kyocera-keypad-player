#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/.."
bash tests/run_dev9_feature_smoke.sh
python3 tests/test_bluetooth_probe_source.py
