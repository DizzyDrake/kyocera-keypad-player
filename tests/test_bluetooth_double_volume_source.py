#!/usr/bin/env python3
"""Source-only static wiring and containment checks; not Android compile."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
a=(r/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
s=(r/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlaybackService.java').read_text()
g=(r/'app/build.gradle').read_text()
m=(r/'app/src/main/AndroidManifest.xml').read_text()
core=(r/'app/src/main/java/org/roarin/kyocerakeypad/core/VolumeDoubleTapSeek.java').read_text()
cases={
  'same Android applicationId':"applicationId 'org.roarin.kyocerakeypad.sandboxwqa365'" in g,
  'source-only new version':"versionCode 19" in g and "dev16-remote-skip" in g,
  'volume detection default OFF':'settings.getBoolean("double_volume_seek",false)' in s,
  'debug-only settings toggle':'if(BuildConfig.DEBUG) item("Debug: Experimental double VOLUME seek:' in a and 'setVolumeDoubleSeekEnabled(' in a,
  'explanation warns local volume keys':'Phone volume buttons can trigger it too' in a,
  'single index only':'step!=1 && step!=-1' in core,
  'same direction and bounded gap':'firstDirection==step' in core and 'maxGapMs' in core,
  '650ms window':'new VolumeDoubleTapSeek(650L)' in s,
  '100ms samples while playing':'playing?100L:500L' in s,
  'requires active playback':'if(playing && !btProbeActive)' in s,
  'forward 30s':'seek(30000L)' in s and 'return step>0?Action.BACK_15S:Action.FORWARD_30S;' in core,
  'backward 15s':'seek(-15000L)' in s and 'return step>0?Action.BACK_15S:Action.FORWARD_30S;' in core,
  'normal volume unchanged':'setStreamVolume(' not in s and 'adjustStreamVolume(' not in s,
  'no remote audio routing':'setPlaybackToRemote(' not in s,
  'keeps existing media control dispatcher':'new MediaTransportSequencer(350)' in s,
  'existing diagnostic still available':'BT_PROBE_LENGTH_MS=45000L' in s and 'Debug: Record Bluetooth volume/keys (45s)' in a,
  'disable samples after shutdown':'handler.removeCallbacks(volumeDoubleSeekPoll)' in s and 'volumeDoubleSeekEnabled=false;' in s,
  'no new Bluetooth or internet permissions':'android.permission.BLUETOOTH' not in m and 'android.permission.INTERNET' not in m,
  'no new package name':'org.roarin.kyocerakeypad.sandboxwqa365' in g,
}
for k,v in cases.items():print(('PASS' if v else 'FAIL'),k)
print('ASSERT',sum(cases.values()),'/',len(cases))
assert all(cases.values())
