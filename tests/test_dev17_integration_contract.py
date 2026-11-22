#!/usr/bin/env python3
"""DEV17 static Android source contracts, without pretending to execute Android framework code."""
from pathlib import Path
import re, xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
service=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlaybackService.java').read_text()
ui=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
focus=(root/'app/src/main/java/org/roarin/kyocerakeypad/core/AudioFocusGate.java').read_text()
build=(root/'app/build.gradle').read_text()
manifest=(root/'app/src/main/AndroidManifest.xml').read_text()
workflow=(root/'.github/workflows/dev17-unsigned-local-sign.yml').read_text()
checks=[]
def ck(label, ok):
    checks.append((label,bool(ok)))
    if not ok: print('FAIL',label)
# Completion -> new player must never stop foreground ownership midway through a track switch.
release=service.split('private boolean releaseForTrackHandoff(){',1)[1].split('private boolean playFromInternal(',1)[0]
play=service.split('private boolean playFromInternal(',1)[1].split('private void commitAudibleResumePosition',1)[0]
stop=service.split('boolean stopPlayer(){',1)[1].split('void pause(){',1)[0]
loss=service.split('private void focusChanged(int change){',1)[1].split('void abandonFocus(){',1)[0]
pause=service.split('void pause(){',1)[1].split('void explicitPlay(){',1)[0]
remove=service.split('private void releaseAfterCommittedRemoval(boolean continuing){',1)[1].split('boolean playPlaylist(',1)[0]
ck('handoff avoids stopSelf and retireForeground', all(v not in release for v in ('retireForeground(','stopSelf(','stopPlayer(')))
ck('handoff releases MediaPlayer',all(v in release for v in ('old.reset()','old.release()','persist()')))
ck('playFromInternal uses handoff', 'releaseForTrackHandoff()' in play and 'if(!stopPlayer())' not in play)
ck('completed track selects a successor', 'playFromInternal(live.id,nextIndex,false)' in play)
ck('manual stop still retires foreground','retireForeground()' in stop)
ck('playlist removal preserves service if continuing','if(!continuing)retireForeground()' in remove)
ck('focus callbacks retain request after short loss','focusGate.onTransientLoss()' in loss and 'transientResumePending|=wasRequested' in loss)
ck('focus gain resumes only eligible current session','if(!transientResumePending)return;' in loss and 'playbackGate.requestPlay()' in loss and 'if(prepared && !awaitingInitialSeek)' in loss)
ck('focus gain rejected in call modes','if(phoneCallMode() || player==null)' in loss)
ck('permanent focus loss not auto resumed', 'focusGate.onLoss()' in loss and 'abandonFocus();keepPausedControls()' in loss)
ck('explicit user pause cancels transient restart','transientResumePending=false;' in pause and 'abandonFocus()' in pause)
ck('focus gate never autoclears permanent loss','if(transientInterrupted) interrupted = false;' in focus and 'transientInterrupted = false;' in focus)
ck('initial seek completion guard','awaitingInitialSeek=true;' in play and 'awaitingInitialSeek=false;' in play)
ck('preserve independent BT skip defaults','remoteSeekBook=settings.getBoolean("remote_seek_book",true)' in service and 'remoteSeekMusic=settings.getBoolean("remote_seek_music",false)' in service)
ck('application identity unchanged with upgrade',"applicationId 'org.roarin.kyocerakeypad.sandboxwqa365'" in build and 'versionCode 20' in build)
ck('local sign only and manual workflow', 'workflow_dispatch:' in workflow and 'app-release-unsigned.apk' in workflow and 'upload-artifact@v4' in workflow and "versionCode='20'" in workflow)
ck('lane palette', '#A85608' in ui and '#142B49' in ui and 'book?BOOK_NAVY:MUSIC_ORANGE' in ui)
ck('adaptive icon declared','android:icon="@mipmap/ic_launcher"' in manifest)
ck('no INTERNET permission','android.permission.INTERNET' not in manifest)
for path in ('app/src/main/res/values/colors.xml','app/src/main/res/drawable/ic_dumbplayer_play_foreground.xml','app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml'):
    ck(path+' XML parses', (ET.parse(root/path) is not None))
icon=(root/'app/src/main/res/drawable/ic_dumbplayer_play_foreground.xml').read_text()
ck('owner triangle white outline', '#FF8C00' in icon and '#FFFFFFFF' in icon)
ck('owner navy icon background', '#142B49' in (root/'app/src/main/res/values/colors.xml').read_text())
for name,okay in checks: print(('PASS' if okay else 'FAIL'),name)
print('DEV17 source contracts',sum(ok for _,ok in checks),'/',len(checks))
assert all(ok for _,ok in checks)
