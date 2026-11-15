#!/usr/bin/env python3
"""Source-contract checks for DEV14. Android compilation/device use NOT claimed."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
a=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
s=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlaybackService.java').read_text()
policy=(root/'app/src/main/java/org/roarin/kyocerakeypad/core/PlaylistRemovalPolicy.java').read_text()
order=(root/'app/src/main/java/org/roarin/kyocerakeypad/core/PlaylistPlaybackOrder.java').read_text()
g=(root/'app/build.gradle').read_text()
checks={
'candidate v18 retains original app identity':"versionCode 19" in g and "versionName '0.3.0-dev16-remote-skip'" in g and "applicationId 'org.roarin.kyocerakeypad.sandboxwqa365'" in g,
'distinct music and book shuffle settings':'private boolean shuffleMusic, shuffleBook' in s and 'settings.getBoolean("shuffle_music",legacyShuffle)' in s and 'settings.getBoolean("shuffle_book",legacyShuffle)' in s,
'preferences stored separately':'.putBoolean(book?"shuffle_book":"shuffle_music",enabled)' in s,
'nonactive toggle cannot change session': 'if(activeBook==book){' in s,
'music playlist toggle scoped':'playback.setShuffle(p.audiobook,!playback.shuffleEnabled(p.audiobook))' in a,
'now playing toggle scoped':'playback.setShuffle(activeBook,!playback.shuffleEnabled(activeBook))' in a,
'home/back do not pause':'case "NOW":showHome();break;' in a and 'Main menu (keeps playing)' in a and 'pauseForNavigation()' not in a,
'home link not saved order':'Return to Now Playing (keeps playing)' in a and 'if(row>=homeOrder.size()){' in a,
'active list navigation':'private void openPlayingPlaylist(){' in a and 'reset("PLAYING_LIST")' in a and 'showPlayingTrackActions(p.id,id)' in a,
'active list uses session shuffle when valid':'playback.playbackOrderSnapshot()' in a and 'session.containsAll(p.entries)' in a,
'active list keyboard return':'case "PLAYING_LIST":case "PLAYING_ITEM":' in a,
'play selected track is explicit':'item("▶ Play this track now"' in a and 'playFrom(live,index,false)' in a,
'remove requires explicit confirmation':'.setPositiveButton("Remove"' in a and 'removePlaylistTrack(playlistId,index,key)' in a,
'service writes detached copy before releasing player':'StateMutation.prepareAndSave(state,draft->' in s and s.index('StateMutation.prepareAndSave(state,draft->')<s.index('releaseAfterCommittedRemoval()'),
'service refuses stale track key':'!playlist.entries.get(index).equals(expectedKey)' in s,
'active shuffle order retains survivors':'playbackOrder.removeEntry(playlistId,expectedKey);' in s and 'order.remove(key);' in order,
'current removal never writes old media position into new track':'private void releaseAfterCommittedRemoval(){' in s and 'player=null;prepared=false;' in s,
'no file delete in removal service': 'delete(' not in s.split('boolean removePlaylistTrack(',1)[1].split('private void releaseAfterCommittedRemoval()',1)[0],
'legacy progress still separately saved':'final Progress music' in (root/'app/src/main/java/org/roarin/kyocerakeypad/core/PlayerState.java').read_text(),
'double next hidden in release':'if(BuildConfig.DEBUG){' in a and 'experimentalDoubleNext=BuildConfig.DEBUG &&' in s,
'bluetooth recorder hidden in release':'if(BuildConfig.DEBUG) item("Debug: Record Bluetooth volume/keys (45s)"' in a,
'double volume explicitly debug-only':'if(BuildConfig.DEBUG) item("Debug: Experimental double VOLUME seek:' in a and 'volumeDoubleSeekEnabled=BuildConfig.DEBUG &&' in s,
'signing secret not in code':'KEYSTORE_PASSWORD=' not in a and 'KEYSTORE_PASSWORD=' not in s,
}
for key,passed in checks.items():print(('PASS ' if passed else 'FAIL ')+key)
print('DEV14 source checks',sum(checks.values()),'/',len(checks))
assert all(checks.values()),'DEV14 source contracts not met'
