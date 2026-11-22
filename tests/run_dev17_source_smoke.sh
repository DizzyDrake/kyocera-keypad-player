#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Host checks only; does not run Android SDK or phone-specific callbacks.
set -euo pipefail
cd "$(dirname "$0")/.."
tmpdir=$(mktemp -d);trap 'rm -rf "$tmpdir"' EXIT
javac --release 8 -d "$tmpdir" app/src/main/java/org/roarin/kyocerakeypad/core/*.java tests/*Tests.java
for test in tests/*Tests.java; do java -cp "$tmpdir" "$(basename "$test" .java)";done
# Historical DEV15 static test asserted no autoresume, so DO NOT rerun it
# as if it applied to DEV17 (the user explicitly reversed that requirement).
# Older DEV13/14/15 static contracts also pin historical version numbers,
# old method signatures and no-autoresume behavior. Keep them for provenance,
# but run the current DEV17 comprehensive contract and independent checks here.
for test in tests/test_dev17_integration_contract.py tests/test_dev16_remote_skip_source.py tests/test_library_availability_source.py tests/test_stale_import_source.py; do python3 "$test";done
echo 'DEV17 host-only checks complete. Android compile / device tests NOT performed.'
