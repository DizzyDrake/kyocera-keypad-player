#!/usr/bin/env python3
"""DEV6 adaptation of DEV5 static integration checks, not an Android SDK build or phone trial."""
from pathlib import Path
root=Path(__file__).resolve().parent.parent
p=root/'app/src/main/java/org/roarin/kyocerakeypad'
a=(p/'KeypadPlayerActivity.java').read_text()
s=(p/'KeypadPlaybackService.java').read_text()
o=(p/'core/PlaylistPlaybackOrder.java').read_text()
g=(root/'app/build.gradle').read_text()
m=(root/'app/src/main/AndroidManifest.xml').read_text()
checks={
 'Existing sandbox identity preserved':"applicationId 'org.roarin.kyocerakeypad.sandboxwqa365'" in g,
 'Version code incremented': 'versionCode 9' in g,
 'Explicit Play Playlist action': 'item("▶ Play playlist",()->playPlaylist(p));' in a,
 'Right shortcut on DETAIL': '"DETAIL".equals(screen)' in a and 'key==KeyEvent.KEYCODE_DPAD_RIGHT' in a,
 'Right shortcut on PLAYLISTS': '"PLAYLISTS".equals(screen)' in a and 'playlistRowIds.get(row)' in a,
 'No autoplay on bind': 'showHome();' in a and 'playPlaylist(' not in a.split('onServiceConnected',1)[1].split('onServiceDisconnected',1)[0],
 'Shuffle switch exposed': 'item("Shuffle: "+' in a and 'playback.setShuffle(!playback.shuffleEnabled())' in a,
 'Repeat switch exposed': 'item("Repeat: "+repeatLabel()' in a and 'playback.cycleRepeat()' in a,
 'Now Playing state': 'Shuffle "+(playback!=null' in a and 'Repeat "+repeatLabel()' in a,
 'Saved order not modified': 'Collections.shuffle(fresh, random)' in o and 'new ArrayList<>(savedEntries)' in o,
 'End-of-list uses mode': 'playbackOrder.next(key,1,repeatMode,true)' in s,
 'Current progress checked on completion': 'key.equals(progress.trackKey)' in s and 'p.id.equals(progress.playlistId)' in s,
 'Manual NEXT uses queue': 'playbackOrder.next(p.trackKey,delta,repeatMode,false)' in s,
 'Mode saved in app preferences': '.putString("repeat",repeatMode.name())' in s and '.putBoolean("shuffle",enabled)' in s,
 'Optional double NEXT off by default': 'getBoolean("double_next_seek",false)' in s,
 'Single NEXT flush scheduled': 'handler.postDelayed(mediaFlush,delay)' in s and 'transport.flush(SystemClock.elapsedRealtime())' in s,
 'Headset volume not hijacked': 'KEYCODE_VOLUME_DOWN' not in s and 'KEYCODE_VOLUME_UP' not in s,
 'Existing focus guard': 'CompletionPolicy.mayAdvance(playbackGate,focusGate)' in s,
 'Existing foreground service': 'foregroundServiceType="mediaPlayback"' in m,
 'No Internet permission': 'android.permission.INTERNET' not in m,
}
for name,ok in checks.items():print(('PASS' if ok else 'FAIL')+' '+name)
print('TOTAL',sum(checks.values()),'/',len(checks))
assert all(checks.values())
