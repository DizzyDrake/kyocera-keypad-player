from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
S=(ROOT/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlaybackService.java').read_text()
A=(ROOT/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
P=(ROOT/'app/src/main/java/org/roarin/kyocerakeypad/core/RemoteSkipPolicy.java').read_text()
checks=[]
def check(label,flag):
 assert flag,label
 checks.append(label)
check('audiobook default on', 'remoteSeekBook=settings.getBoolean("remote_seek_book",true)' in S)
check('music default off','remoteSeekMusic=settings.getBoolean("remote_seek_music",false)' in S)
check('persist audiobook lane','putBoolean(book?"remote_seek_book":"remote_seek_music",enabled)' in S)
check('independent mutation','if(book)remoteSeekBook=enabled;else remoteSeekMusic=enabled;' in S)
check('use audio lane flag','RemoteSkipPolicy.decide(activeBook,remoteSeekMusic,remoteSeekBook,next)' in S)
check('media next callback route','onSkipToNext(){ btProbeNote("MediaSession.onSkipToNext"); remoteNextPrevious(true); }' in S)
check('media previous callback route','onSkipToPrevious(){ btProbeNote("MediaSession.onSkipToPrevious"); remoteNextPrevious(false); }' in S)
check('sequencer next routed','case NEXT: remoteNextPrevious(true);break;' in S)
check('sequencer previous routed','case PREVIOUS: remoteNextPrevious(false);break;' in S)
check('notification next routed','ACTION_NEXT.equals(action))remoteNextPrevious(true)' in S)
check('notification previous routed','ACTION_PREVIOUS.equals(action))remoteNextPrevious(false)' in S)
check('seek forward interval','case SEEK_FORWARD_30S: seek(30000L);break;' in S)
check('seek back interval','case SEEK_BACK_15S: seek(-15000L);break;' in S)
check('track fallback next','case NEXT_TRACK: skip(1);break;' in S)
check('track fallback previous','case PREVIOUS_TRACK: skip(-1);break;' in S)
check('notification seek labels',S.count('remoteSeekEnabled(activeBook)?')>=2)
check('both lane toggles settings','Bluetooth Next/Previous · Audiobooks:' in A and 'Bluetooth Next/Previous · Music:' in A)
check('nowplaying one click toggle','Bluetooth Next/Previous:' in A and 'playback.setRemoteSeek(activeBook,!playback.remoteSeekEnabled(activeBook));showNow();' in A)
check('local keypad track keys preserved',all(x in A for x in ['KEYCODE_4','KEYCODE_6','playback.skip(-1);showNow();','playback.skip(1);showNow();']))
check('volume experiment still debug gated','volumeDoubleSeekEnabled=BuildConfig.DEBUG' in S)
check('no destructive media operations',not any(x in P for x in ['deleteFile','deleteAudio','removePlaylistTrack']))
check('no automatic play on remote seek','explicitPlay' not in P)
print('PASS',len(checks),'DEV16 source-level checks')
