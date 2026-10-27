#!/usr/bin/env python3
"""Source-level sanity checks only; do NOT substitute for Android compilation."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
s=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
manifest=(root/'app/src/main/AndroidManifest.xml').read_text()
checks={
  'explicit play gate in prepared callback': 'else if(canStartPlayback())mp.start();' in s,
  'initial seek listener cleared': 'seeked.setOnSeekCompleteListener(null);' in s,
  'seek completion foreground gated': 'if(player==seeked && canStartPlayback())seeked.start();' in s,
  'manual play foreground gated': 'if(canStartPlayback())player.start();' in s,
  'both foreground and focus required': 'return playbackGate.canStart() && audioFocusGate.canStart();' in s,
  'pause clears request': 'playbackGate.onPause();' in s,
  'resume does not request playback': 'playbackGate.onResume();' in s,
  'Back from now playing pauses': 'case "NOW":pauseForNavigation();showHome();break;' in s,
  'only declared permission is external storage read': re.findall(r'<uses-permission\s+android:name="([^"]+)',manifest)==['android.permission.READ_EXTERNAL_STORAGE'],
  'no external network permission': 'android.permission.INTERNET' not in manifest,
}
for name,ok in checks.items():
    print(('PASS' if ok else 'FAIL')+' static '+name)
assert all(checks.values()), 'Source guard check failed'
print(f'PASS {len(checks)} static checks (NOT Android compilation)')
