#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Read-only verification for GitHub upload-ready source tree. Does not build/sign APK."""
from pathlib import Path
import re, subprocess, sys
r = Path(__file__).resolve().parent
required = [
  'app/build.gradle', 'settings.gradle', 'build.gradle',
  'app/src/main/AndroidManifest.xml',
  'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java',
  'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlaybackService.java',
  'app/src/main/java/org/roarin/kyocerakeypad/core/RemoteSkipPolicy.java',
  'tests/RemoteSkipPolicyTests.java', 'tests/ActivePlaylistEditTests.java',
  'tests/run_dev16_source_smoke.sh',
  '.github/workflows/dev16-unsigned-local-sign.yml',
  'WQ439_VERIFY_FULL_SOURCE.py','00_START_HERE_GITHUB_DEV16_20261115.md',
  'UPLOAD_TO_EXISTING_GITHUB.cmd','PUSH_DEV16_TO_GITHUB.ps1'
]
missing = [p for p in required if not (r/p).is_file()]
if missing: sys.exit('FAIL missing: ' + ', '.join(missing))
gradle = (r/'app/build.gradle').read_text()
assert re.search(r"applicationId\s+'org\.roarin\.kyocerakeypad\.sandboxwqa365'",gradle)
assert re.search(r'versionCode\s+19\b',gradle)
wf = (r/'.github/workflows/dev16-unsigned-local-sign.yml').read_text()
assert 'workflow_dispatch:' in wf and ':app:assembleRelease' in wf
assert 'tests/run_dev16_source_smoke.sh' in wf and "versionCode='19'" in wf
assert 'upload-artifact@v4' in wf
source = (r/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
for s in ['View playing playlist','Return to Now Playing','Remove from playlist','remoteSeekEnabled']:
    assert s in source,s
service = (r/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlaybackService.java').read_text()
for s in ['remote_seek_book','remote_seek_music','remoteSeekBook=true','remoteSeekMusic=false']:
    assert s in service,s
assert (r/'app/src/main/java/org/roarin/kyocerakeypad/core/RemoteSkipPolicy.java').is_file()
ret = subprocess.run([sys.executable,str(r/'WQ439_VERIFY_FULL_SOURCE.py')],cwd=str(r),capture_output=True,text=True)
if ret.returncode: sys.exit('FAIL original DEV16 source verification: ' + ret.stdout+ret.stderr)
print(ret.stdout.strip())
print('PASS: GitHub source root, workflow, versionCode19, DEV14-16 features')
