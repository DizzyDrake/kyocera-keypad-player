#!/usr/bin/env python3
"""Source-level Android lifecycle contracts; not physical SMS/Bluetooth tests.

The earlier regressions remain available in previous full DEV14 source; this test
makes future accidental regressions in interrupted playback visible.
"""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlaybackService.java').read_text()
a=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
g=(root/'app/build.gradle').read_text()
m=(root/'app/src/main/AndroidManifest.xml').read_text()
focus=(root/'app/src/main/java/org/roarin/kyocerakeypad/core/AudioFocusGate.java').read_text()

pause=s.split('    void pause(){',1)[1].split('    void explicitPlay(){',1)[0]
loss=s.split('    private void focusChanged(int change){',1)[1].split('    void abandonFocus(){',1)[0]
keep=s.split('    private void keepPausedControls(){',1)[1].split('    private void retireForeground(){',1)[0]
stop=s.split('    boolean stopPlayer(){',1)[1].split('    void pause(){',1)[0]
start=s.split('    @Override public int onStartCommand(',1)[1].split('    private static MediaTransportSequencer.Key',1)[0]
resume=s.split('    void explicitPlay(){',1)[1].split('    void toggle(){',1)[0]
update=s.split('    private void updateMediaSession(){',1)[1].split('    private Notification notification(){',1)[0]
settings=a.split('    private void showSettings(){',1)[1].split('    private void ',1)[0]
checks={
    'same package ID':"applicationId 'org.roarin.kyocerakeypad.sandboxwqa365'" in g,
    'version increments instead of replacing installed build':'versionCode 19' in g,
    'normal release disables persisted double-volume': 'volumeDoubleSeekEnabled=BuildConfig.DEBUG && settings.getBoolean("double_volume_seek",false)' in s,
    'setter cannot enable double-volume in release':'if(!BuildConfig.DEBUG) enabled=false;' in s,
    'legacy volume poll logic survives only for diagnostic':'new VolumeDoubleTapSeek(650L)' in s and 'if(volumeDoubleSeekEnabled)handler.post(volumeDoubleSeekPoll)' in s,
    'debug-only volume menu':'if(BuildConfig.DEBUG) item("Debug: Experimental double VOLUME seek:' in settings,
    'no release volume menu entry':'        item("Experimental double VOLUME seek:' not in settings,
    'debug-only volume explanation':'if(BuildConfig.DEBUG) item("Debug: Double VOLUME seek explanation"' in settings,
    'physical media buttons intact':'KEYCODE_HEADSETHOOK' in s and 'KEYCODE_MEDIA_PLAY_PAUSE' in s and 'new MediaTransportSequencer(350)' in s,
    'pause keeps paused controls':'keepPausedControls()' in pause and 'retireForeground()' not in pause,
    'focus loss keeps paused controls':'keepPausedControls()' in loss and 'retireForeground()' not in loss,
    'focus gain does not autoplay':'focusGate.onGain();return;' in loss and 'player.start()' not in loss,
    'focus request only on explicit play':'if(requestFocus(activeBook))' in resume,
    'focus rejected still shows resume controls':'keepPausedControls()' in resume,
    'paused controls require prepared player':'if(recoveryMode || !isPrepared()){retireForeground();return;}' in keep,
    'paused controls leave foreground':'stopForeground(false)' in keep,
    'paused controls not stopSelf':'stopSelf(' not in keep,
    'paused controls notify Android':'nm.notify(NOTIFICATION_ID,notification());' in keep,
    'state update retains paused notification':'if(foreground || isPrepared())' in update,
    'notification has play pending intent':'notificationAction(ACTION_TOGGLE,2)' in s and 'getService(this,requestCode' in s,
    'notification is nonongoing when paused':'.setOngoing(isPlaying())' in s,
    'notification MediaStyle tied to live MediaSession':'setMediaSession(mediaSession.getSessionToken())' in s,
    'resume command does not retire prepared pause':'else if (isPrepared() && !isPlaying()) keepPausedControls();' in start,
    'explicit stop removes notification':'retireForeground()' in stop and 'stopSelf();' in s,
    'onDestroy clears stale notification':'((NotificationManager)getSystemService(Context.NOTIFICATION_SERVICE)).cancel(NOTIFICATION_ID);' in s,
    'Android media playback service declared':'android:foregroundServiceType="mediaPlayback"' in m and 'android.permission.FOREGROUND_SERVICE' in m,
    'music may auto duck but books pause':'setWillPauseWhenDucked(book)' in s,
    'no auto resume after process death':'return START_NOT_STICKY;' in s,
    'no network permission':'android.permission.INTERNET' not in m,
    'focus gate still requires explicit user play':'focusGate.onExplicitRequest(granted)' in s and 'interrupted = true;' in focus,
}
for label,ok in checks.items():print(('PASS' if ok else 'FAIL'),label)
print('DEV15 source contract',sum(checks.values()),'/',len(checks))
assert all(checks.values())
