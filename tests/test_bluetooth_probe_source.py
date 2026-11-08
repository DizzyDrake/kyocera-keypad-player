#!/usr/bin/env python3
"""Offline source-only checks, not a substitute for Android/neckband trials."""
from pathlib import Path
import hashlib
root=Path(__file__).resolve().parents[1]
p=root/'app/src/main/java/org/roarin/kyocerakeypad'
a=(p/'KeypadPlayerActivity.java').read_text()
s=(p/'KeypadPlaybackService.java').read_text()
g=(root/'app/build.gradle').read_text()
m=(root/'app/src/main/AndroidManifest.xml').read_text()
checks={
    'same package identity':"applicationId 'org.roarin.kyocerakeypad.sandboxwqa365'" in g,
    'new version code 16':'versionCode 16' in g,
    'unchanged Bluetooth media transport timing':'new MediaTransportSequencer(350)' in s,
    'manual opt-in 45s window':'Record Bluetooth volume/keys (45s)' in a and 'BT_PROBE_LENGTH_MS=45000L' in s,
    'no opt-in when paused':'if(!playback.isPlaying())' in a,
    '100ms bounded observation':'BT_PROBE_SAMPLE_MS=100L' in s,
    'music volume read only':'getStreamVolume(AudioManager.STREAM_MUSIC)' in s,
    'media callback logging':'btProbeNote("MediaSession.onMediaButtonEvent key="' in s,
    'captures transport callbacks':'btProbeNote("MediaSession.onSkipToNext")' in s,
    'transfer folder output':'getExternalFilesDir("transfer")' in s and 'bt_probe_' in s,
    'unregisters sampling on close':'finishBluetoothDiagnostic("Service closed before 45s")' in s,
    'no new audio routing':'setPlaybackToRemote' not in s,
    'no programmatic volume change':'adjustStreamVolume(' not in s and 'setStreamVolume(' not in s,
    'no new permissions':'android.permission.BLUETOOTH' not in m and 'android.permission.INTERNET' not in m,
    "diagnostic retained and new feature disclosed":"The DEV11 diagnostic still records" in (root/"README.md").read_text(),
}
for name,ok in checks.items():print(('PASS' if ok else 'FAIL'),name)
print(f'{sum(checks.values())}/{len(checks)} diagnostic source assertions')
assert all(checks.values())
