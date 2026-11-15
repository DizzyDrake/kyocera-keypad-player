from pathlib import Path
root=Path(__file__).resolve().parents[1]
a=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
s=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlaybackService.java').read_text()
g=(root/'app/build.gradle').read_text()
checks={
 'now screen dispatch gated':'"NOW".equals(screen) && !(getCurrentFocus() instanceof EditText)' in a,
 'down once and repeats consumed':'event.getAction()==KeyEvent.ACTION_DOWN && event.getRepeatCount()==0' in a,
 'seek back':'case KeyEvent.KEYCODE_1:seekBy(-10000)' in a,
 'seek forward':'case KeyEvent.KEYCODE_3:seekBy(10000)' in a,
 'previous track':'case KeyEvent.KEYCODE_4:playback.skip(-1)' in a,
 'next track':'case KeyEvent.KEYCODE_6:playback.skip(1)' in a,
 'play pause':'case KeyEvent.KEYCODE_5:' in a and 'playback.toggle();showNow()' in a,
 'bookmark only audiobook':'if(activeBook)saveQuickBookmark()' in a,
 'previous bookmark':'case KeyEvent.KEYCODE_7:if(activeBook)jumpBookmark(-1)' in a,
 'next bookmark':'case KeyEvent.KEYCODE_9:if(activeBook)jumpBookmark(1)' in a,
 'browse bookmarks':'case KeyEvent.KEYCODE_POUND:if(activeBook)showBookmarks()' in a,
 'service snapshot non mutating':'List<String> playbackOrderSnapshot(){return playbackOrder.snapshot();}' in s,
 'adjacent title':'"Prev"+orderHint' in a and '"Next"+orderHint' in a,
 'duration':'clock(t.durationMs)' in a and '"unknown"' in a,
 'footer key legend':'"1 -10s · 3 +10s · 4 Prev · 6 Next · 5 Play/Pause · Back = menu"' in a,
 'bookmark no rename dialog on quick save':'next->next.addBookmark(key,clock(at),at)' in a,
 'original bookmark edit preserved':'item("Rename bookmark"' in a and 'item("Delete bookmark"' in a,
 'parent sleep timer preserved':'sleepDeadlineElapsed=now+duration;' in s,
 'parent rewind preserved':'(resume && p.audiobook)' in s,
 'parent shuffle preserved':'void setShuffle(boolean book,boolean enabled)' in s,
 'parent repeat preserved':'void cycleRepeat()' in s,
 'parent service background':'startForegroundService(new Intent(this,KeypadPlaybackService.class))' in a,
 'same sandbox app ID':"applicationId 'org.roarin.kyocerakeypad.sandboxwqa365'" in g,
 'version code bumped':'versionCode 17' in g and "versionName '0.2.8-dev14-playlist-navigation'" in g,
}
for name,passed in checks.items():print(('PASS' if passed else 'FAIL'),name)
assert all(checks.values())
print(f'{len(checks)}/{len(checks)} DEV8 inherited Now Playing checks PASS')
