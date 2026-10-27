"""Conservative static checks only: Android Activity is NOT compiled or run."""
from pathlib import Path
s=Path('app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
manifest=Path('app/src/main/AndroidManifest.xml').read_text()
checks={
    'focus request API29': 'new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN)' in s,
    'music/speech audio attributes': 'CONTENT_TYPE_SPEECH:AudioAttributes.CONTENT_TYPE_MUSIC' in s,
    'explicit focus denial stops play': 'if(!requestAudioFocusForExplicitPlay(p.audiobook))' in s,
    'manual resume focus request': 'else if(requestAudioFocusForExplicitPlay(activeBook))' in s,
    'prepared callback double gate': 'else if(canStartPlayback())mp.start();' in s,
    'seek complete callback double gate': 'if(player==seeked && canStartPlayback())seeked.start();' in s,
    'loss transient handled': 'change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT ||' in s,
    'duck treated as pause': 'change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK' in s,
    'focus loss calls MediaPlayer.pause': 'if(player.isPlaying())player.pause();' in s,
    'loss persists position': 'saveActivePosition();\n            persist();' in s,
    'gain does not start': 'audioFocusGate.onGain(); // Explicit Play still required after interruption.' in s,
    'abandon on navigation': 'saveActivePosition();persist();\n        abandonAudioFocus();' in s,
    'stale callback epoch guard': 'if(requestEpoch==focusEpoch)onAudioFocusChanged(change);' in s,
    'call mode defensive guard': 'mode==AudioManager.MODE_RINGTONE || mode==AudioManager.MODE_IN_CALL' in s and 'mode==AudioManager.MODE_IN_COMMUNICATION' in s,
    'no telephony permission': 'READ_PHONE_STATE' not in manifest and 'READ_CALL_LOG' not in manifest,
    'no SMS permission': 'READ_SMS' not in manifest and 'RECEIVE_SMS' not in manifest,
}
for name,ok in checks.items():
    assert ok,name
    print('PASS static:',name)
print(f'PASS {len(checks)} static audio focus checks (NOT Android compilation)')
