from pathlib import Path
p=Path(__file__).resolve().parents[1]/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java'
s=p.read_text()
checks={
    'Right key intercepted only on library': '"LIBRARY".equals(screen) && key==KeyEvent.KEYCODE_DPAD_RIGHT' in s,
    'Left key intercepted only in index': '"ALPHABET".equals(screen) && key==KeyEvent.KEYCODE_DPAD_LEFT' in s,
    'single press avoids repeat': s.count('event.getRepeatCount()==0')==2,
    'picker preserves selected position': 'libraryReturnSelection=Math.max(0,list.getSelectedItemPosition());' in s,
    'index respects filtered library': 'visibleLibraryTitles.add(t.title);' in s and 'if(!hay.contains(f))continue;' in s,
    'index does not use keyboard prompt': 'private void showAlphabetIndex()' in s and 'AlphabetJump.counts(visibleLibraryTitles)' in s,
    'jump targets first track after filter row': 'selectLibraryPosition(index+1)' in s,
    'Back exits index': 'case "ALPHABET":restoreLibrary();break;' in s,
    'left exits index': 'key==KeyEvent.KEYCODE_DPAD_LEFT' in s and 'restoreLibrary();' in s,
    'async focus selection screen guarded': 'if("LIBRARY".equals(screen)){' in s,
    'no autoplay introduced in index': 'private void jumpToLibraryLetter(char letter)' in s and 'playFrom(' not in s.split('private void jumpToLibraryLetter(char letter)')[1].split('private void restoreLibrary()')[0],
    'existing sorted library intact': 'sorted.sort((a,b)->a.title.compareToIgnoreCase(b.title));' in s,
    'existing typed search intact': 'Filter by title / artist / album / folder' in s,
    'playlist add via explicit guarded helper': 'addTrackAndPersist(selectedPlaylist,key)' in s and 'state.add(playlistId,key)' in s and 'p.entries.remove(key)' in s,
    'existing list focus intact': 'list.setItemsCanFocus(false);list.setSelection(0);list.requestFocus();' in s,
}
for name,ok in checks.items(): print(('PASS' if ok else 'FAIL')+' '+name)
assert all(checks.values())
print('PASS',len(checks),'static integration checks (NOT Android/device validation)')
