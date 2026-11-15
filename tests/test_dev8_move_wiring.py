#!/usr/bin/env python3
"""Focused source wiring checks, NOT Android SDK compile or physical E4831 tests."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
a=(r/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
s=(r/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlaybackService.java').read_text()
d=(r/'app/src/main/java/org/roarin/kyocerakeypad/core/PlaylistReorderDraft.java').read_text()
g=(r/'app/build.gradle').read_text()
checks={
 'in-list mode visible':'reset("MOVE")' in a and '> MOVING ' in a,
 'selected item kept visible':'list.setSelectionFromTop(selected' in a,
 'stable selected track key':'draft.selectedKey()' in a and 'selectedKey' in d,
 'star only detail':'"DETAIL".equals(screen) && key==KeyEvent.KEYCODE_STAR' in a,
 'star row excludes command rows':'list.getSelectedItemPosition()-detailTrackStartRow' in a,
 'action menu can enter mode':'item("Move in playlist (keypad Move Mode)"' in a,
 'D-pad up moves':'case KeyEvent.KEYCODE_DPAD_UP:moved=moveDraft.moveBy(-1)' in a,
 'D-pad down moves':'case KeyEvent.KEYCODE_DPAD_DOWN:moved=moveDraft.moveBy(1)' in a,
 'top shortcut':'case KeyEvent.KEYCODE_1:moved=moveDraft.moveTop()' in a,
 'bottom shortcut':'case KeyEvent.KEYCODE_9:moved=moveDraft.moveBottom()' in a,
 'save center':'key==KeyEvent.KEYCODE_DPAD_CENTER' in a and 'saveMoveMode()' in a,
 'cancel CLR Back':'key==KeyEvent.KEYCODE_DEL' in a and 'key==KeyEvent.KEYCODE_BACK' in a,
 'key-up swallowed':'if(event.getAction()==KeyEvent.ACTION_DOWN)' in a and 'return true;' in a,
 'cancel without persistence':'private void cancelMoveMode(){leaveMoveMode();}' in a,
 'commit once':'commitMutation("Save playlist order",draft::apply)' in a,
 'stale list guard':'draft.matchesCurrent(current.entries)' in a and 'p.entries.equals(original)' in d,
 'AtomicFile mutation path':'StateMutation.prepareAndSave(state,edit,this::writeStateBytes)' in a,
 'draft snapshot isolated':'new ArrayList<>(entries)' in d,
 'saved order changes only entries':'p.entries.clear();' in d and 'p.entries.addAll(order);' in d,
 'service refresh after save':'playback.onPlaylistOrderSaved(draft.playlistId())' in a,
 'nonshuffle service refresh':'if(!shuffleEnabled(activeBook) && p!=null' in s and 'playbackOrder.start(p.id,p.entries,progress.trackKey,false,shuffleRandom)' in s,
 'no autoplay on save':'void onPlaylistOrderSaved(String playlistId)' in s and 'player.start()' not in s.split('void onPlaylistOrderSaved(String playlistId)',1)[1].split('void cycleRepeat()',1)[0],
 'move mode back':'case "MOVE":cancelMoveMode();break;' in a,
 'android valid headset hook constant':'KeyEvent.KEYCODE_HEADSETHOOK' in s and 'KEYCODE_HEADSETPHOOK' not in s,
 'source version code':"versionCode 17" in g,
 'source version name':"versionName '0.2.8-dev14-playlist-navigation'" in g,
}
for label,ok in checks.items():print(('PASS' if ok else 'FAIL')+' '+label)
assert all(checks.values()),'DEV8 Move Mode source wiring check failed'
print(f'{len(checks)}/{len(checks)} DEV8 Move Mode wiring checks PASS')
