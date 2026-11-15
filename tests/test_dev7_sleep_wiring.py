from pathlib import Path
root=Path(__file__).resolve().parents[1]
a=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
s=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlaybackService.java').read_text()
b=(root/'app/build.gradle').read_text()
checks={
 'home listening settings':'item("Listening settings",this::showSettings)' in a,
 'rewind settings choices':'playback.cycleAudiobookRewind()' in a,
 'sleep in now playing':'item("Sleep timer: "+sleepTimerLabel(),this::showSleepTimerOptions)' in a,
 'sleep presets':'"10 minutes", "15 minutes", "30 minutes", "60 minutes", "Custom minutes"' in a,
 'custom integer keypad':'android.text.InputType.TYPE_CLASS_NUMBER' in a,
 'timer service elapsed realtime':'sleepDeadlineElapsed=now+duration;' in s and 'SystemClock.elapsedRealtime()' in s,
 'timer expiry pauses':'if (sameSession) pause();' in s,
 'timer expiration guards session':'sleepPlaylistId.equals(p.playlistId)' in s,
 'timer follows same playlist':'sleepBook!=p.audiobook || !sleepPlaylistId.equals(p.id)' in s,
 'timer process-death no restoration':'sleepDeadlineElapsed = -1L;' in s,
 'timer onDestroy cleared':'clearSleepTimer();handler.removeCallbacks(saveTick)' in s,
 'rewind defaults off':'settings.getInt("audiobook_resume_rewind_seconds",0)' in s,
 'rewind only audiobook resume':'(resume && p.audiobook)' in s,
 'rewind canonical progress preserved until started':'state.select(activeBook,p.id,key,start)' in s and 'commitAudibleResumePosition(at)' in s,
 'rewind setting persisted':'putInt("audiobook_resume_rewind_seconds",audiobookRewindSeconds)' in s,
 'existing play playlist preserved':'boolean playPlaylist(String playlistId)' in s,
 'existing shuffle preserved':'void setShuffle(boolean book,boolean enabled)' in s,
 'existing headset option preserved':'void setExperimentalDoubleNext(boolean enabled)' in s,
 'sandbox app ID preserved':"applicationId 'org.roarin.kyocerakeypad.sandboxwqa365'" in b,
 'version bumped':'versionCode 10' in b and "versionName '0.2.1-dev7-wqb429-now-playing-source'" in b,
}
for label,ok in checks.items():
 print(('PASS' if ok else 'FAIL')+' '+label)
assert all(checks.values()),'source wiring failed'
print(f'{len(checks)}/{len(checks)} wiring checks PASS')
