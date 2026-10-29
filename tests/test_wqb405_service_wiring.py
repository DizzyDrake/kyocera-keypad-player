#!/usr/bin/env python3
"""Static source-only checks; NEVER label these Android compile or device tests."""
from pathlib import Path
import re
root=Path(__file__).resolve().parent.parent
activity=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
service=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlaybackService.java').read_text()
manifest=(root/'app/src/main/AndroidManifest.xml').read_text()
gradle=(root/'app/build.gradle').read_text()

def body_after(src, signature, next_signature):
    return src.split(signature,1)[1].split(next_signature,1)[0]
checks={
 'Service owns MediaPlayer': 'MediaPlayer player;' in service and 'MediaPlayer player;' not in activity,
 'Service owns AtomicFile': 'private AtomicFile store;' in service and 'private AtomicFile store;' not in activity,
 'Service owns single PlayerState': 'PlayerState state = new PlayerState();' in service and 'private PlayerState state;' in activity,
 'Activity bind lifecycle': 'bindService(new Intent(this,KeypadPlaybackService.class)' in activity,
 'Activity uses shared service state': 'state=playback.state' in activity and 'playback.state=next' in activity,
 'Activity onPause does not pause normal playback': 'pauseForNavigation()' not in body_after(activity,'@Override public void onPause(){','@Override public void onDestroy(){'),
 'Activity onDestroy does not release normal player': 'stopPlayer()' not in body_after(activity,'@Override public void onDestroy(){','@Override public void onBackPressed(){'),
 'Explicit Home still pauses': 'item("← Home (pauses)",()->{pauseForNavigation();showHome();});' in activity,
 'NOW Back still pauses': 'case "NOW":pauseForNavigation();showHome();break;' in activity,
 'Explicit play starts foreground service': 'startForegroundService(new Intent(this,KeypadPlaybackService.class))' in activity,
 'Service declared not exported': 'android:name=".KeypadPlaybackService" android:exported="false"' in manifest,
 'Foreground permission/type': 'android.permission.FOREGROUND_SERVICE' in manifest and 'foregroundServiceType="mediaPlayback"' in manifest,
 'MediaSession exists': 'new MediaSession(this,' in service and 'mediaSession.setPlaybackState' in service,
 'Media buttons routed via sequencer': 'transport.onPress(mapped,SystemClock.elapsedRealtime())' in service,
 'Double seek not enabled': 'transport.setDoubleSeekEnabled(true)' not in service,
 'Foreground notification has transport actions': 'addAction(previous).addAction(toggle).addAction(next)' in service,
 'Service restart does not autoplay': 'return START_NOT_STICKY;' in service and 'if(!isPrepared())return;' in service,
 'Focus loss pauses and saves': 'focusGate.onLoss();playbackGate.requestPause();' in service and 'savePosition();if (!persist()) error("Position could not be saved");' in service and 'retireForeground();updateMediaSession();notifyChanged();' in service,
 'Focus gain does not auto start': 'if(change==AudioManager.AUDIOFOCUS_GAIN){focusGate.onGain();return;}' in service,
 'Playback tick saves while Activity absent': 'handler.postDelayed(saveTick,5000);' in service and 'if(player!=null && prepared)' in service,
 'AtomicFile recovery preserved': 'store.openRead()' in service and 'store.failWrite(out)' in service,
 'Completion uses current state': 'CompletionPolicy.nextSelection(state,p.id,key,p.audiobook)' in service,
 'Failed-open rollback preserved': 'FailedOpenRollback.attempt(state,book,id,key,previous,this::writeStateBytes)' in service,
 'Existing WQA365 sandbox ID targeted': "applicationId 'org.roarin.kyocerakeypad.sandboxwqa365'" in gradle and "applicationId 'org.roarin.kyocerakeypad.sandboxdev3'" not in gradle,
 'No network permission': 'android.permission.INTERNET' not in manifest,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL')+' static '+k)
print('STATIC_TOTAL',sum(checks.values()),'/',len(checks))
assert all(checks.values())
