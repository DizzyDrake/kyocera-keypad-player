#!/usr/bin/env python3
"""Source contract only: checks actual Activity integration, not Android runtime."""
from pathlib import Path
import re
s=Path(__file__).resolve().parents[1].joinpath('app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
checks={
    'helper import':'import org.roarin.kyocerakeypad.core.FailedOpenRollback;' in s,
    'both callback paths pass expected identity':s.count('restoreUnstartedSelection(p.audiobook,p.id,key,previousProgress,previousActiveBook)')==2,
    'pending callback identity guard':'if(player!=mp)return true;' in s,
    'pre-prepare only':'if(failedBeforePrepared)restoreUnstartedSelection(' in s,
    'helper attempts current state':'FailedOpenRollback.attempt(\n                state,book,pendingPlaylist,pendingTrack,before,this::writeStateBytes)' in s,
    'publish only on restored':'if(rollback.restored()){\n                state=rollback.state;' in s,
    'old unconditional rollback removed':'state.progress(book).restoreFrom(before);' not in s,
    'commit uses copy-persist-publish':'StateMutation.prepareAndSave(state,edit,this::writeStateBytes)' in s,
    'delete UI detaches player first':'if(!stopPlayer())' in s.split('item("Delete playlist"',1)[1].split('int i=0;',1)[0],
    'remove UI can mutate while pending':'commitMutation("Remove track"' in s.split('private void showTrackActions(',1)[1].split('private void showLibrary(',1)[0],
    'navigation pauses without releasing':'stopPlayer()' not in s.split('private void pauseForNavigation(){',1)[1].split('private static AudioAttributes',1)[0],
    'no Android phone permission': 'READ_PHONE_STATE' not in s,
}
for name,ok in checks.items():print(('PASS' if ok else 'FAIL')+' '+name)
assert all(checks.values()),'Activity source wiring contract failed'
