#!/usr/bin/env python3
"""Deterministic source checks for DEV13 integration; NOT an Android SDK build."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
a=(p/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
s=(p/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlaybackService.java').read_text()
core=(p/'app/src/main/java/org/roarin/kyocerakeypad/core/VolumeDoubleTapSeek.java').read_text()
imp=(p/'app/src/main/java/org/roarin/kyocerakeypad/core/PhonePlaylistImport.java').read_text()
g=(p/'app/build.gradle').read_text()
m=(p/'app/src/main/AndroidManifest.xml').read_text()
workflow=(p/'.github/workflows/dev13-update-signed.yml').read_text()
checks={
  'package unchanged':"applicationId 'org.roarin.kyocerakeypad.sandboxwqa365'" in g,
  'new version code': 'versionCode 19' in g,
  'new version name': "versionName '0.3.0-dev16-remote-skip'" in g,
  'header is build-derived': 'render("Dumbplayer · "+displayBuildVersion()' in a and 'BuildConfig.VERSION_NAME' in a,
  'old hardcoded header removed':'DEV10 import trial' not in a,
  'up rewinds 15': 'return step>0?Action.BACK_15S:Action.FORWARD_30S' in core and 'seek(-15000L)' in s,
  'down advances 30': 'return step>0?Action.BACK_15S:Action.FORWARD_30S' in core and 'seek(30000L)' in s,
  'Bluetooth help corrected': 'two quick volume decreases seek forward 30s;' in a and 'two quick increases seek back 15s' in a,
  'volume disabled in ordinary build':'volumeDoubleSeekEnabled=BuildConfig.DEBUG && settings.getBoolean("double_volume_seek",false)' in s,
  'no volume hijacking':'setStreamVolume(' not in s and 'adjustStreamVolume(' not in s,
  'no remote routing':'setPlaybackToRemote(' not in s,
  'stale IDs advisory':'Snapshot ID differs; stale import explicitly allowed.' in a,
  'missing snapshot accepted':'payload.has("expected_snapshot_id")' in a,
  'phone track identities preferred':'target.tracks.containsKey(key)' in imp,
  'missed references reported':'prepared.missingReferences' in a and 'prepared.affectedPlaylists' in a,
  'user confirmation required':'.setPositiveButton("Replace playlists"' in a,
  'preflight happens before stopping':a.index('PhonePlaylistImport.prepare(view.state,specs)')<a.index('if(!playback.stopPlayer())',a.index('PhonePlaylistImport.prepare(view.state,specs)')),
  'file name exact':'pc_playlist_import_v1.json' in imp,
  'only app transfer folder': 'getExternalFilesDir("transfer")' in a,
  'no new network permission': 'android.permission.INTERNET' not in m,
  'signing guard uses uploaded APK fingerprint': 'C7F55F72049E0547354F65816836856735124AB9B46AC73A0265AF099FEFAC16' in workflow,
  'signing mismatch fails': 'if [[ "$cert" != "$DEV12_CERT_SHA256" ]]' in workflow and 'exit 1' in workflow,
  'signing key only in secrets': 'secrets.KYOCERA_DEV12_KEYSTORE_BASE64' in workflow and 'KEYSTORE_B64:' not in g,
  'signing checked before artifact': workflow.index('if [[ "$cert" != "$DEV12_CERT_SHA256" ]]')<workflow.index('actions/upload-artifact@v4'),
  'build workflows separate': (p/'.github/workflows/dev13-compile-check.yml').is_file(),
}
for key,pass_ in checks.items():print(('PASS' if pass_ else 'FAIL')+' '+key)
print(f'INTEGRATION {sum(checks.values())}/{len(checks)}')
assert all(checks.values())
