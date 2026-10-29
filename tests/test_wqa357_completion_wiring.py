"""Offline static Android wiring checks; not a device/SDK test."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
A=(ROOT/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
P=(ROOT/'app/src/main/java/org/roarin/kyocerakeypad/core/CompletionPolicy.java').read_text()
class CompletionWiring(unittest.TestCase):
    def test_current_state_resolution(self):
        b=A.split('player.setOnCompletionListener(mp->{',1)[1].split('player.setOnErrorListener',1)[0]
        self.assertIn('CompletionPolicy.nextSelection(',b)
        self.assertIn('state,p.id,key,p.audiobook)',b)
        self.assertIn('playFrom(next.playlist,next.index,false)',b)
        self.assertNotIn('state.nextIndex(p.id,key)',b)
        self.assertNotIn('playFrom(p,next,false)',b)
    def test_guard_precedes_state_resolution(self):
        b=A.split('player.setOnCompletionListener(mp->{',1)[1].split('player.setOnErrorListener',1)[0]
        self.assertLess(b.index('if(player!=mp)return;'),b.index('CompletionPolicy.mayAdvance('))
        self.assertLess(b.index('CompletionPolicy.mayAdvance('),b.index('CompletionPolicy.nextSelection('))
    def test_helper_is_pure_java_and_checks_context(self):
        self.assertNotIn('android.',P)
        for fragment in ['current.playlistId','current.trackKey','playlist.audiobook!=audiobook',
                         'playlist.entries.indexOf(completedKey)','state.tracks.containsKey']:
            self.assertIn(fragment,P)
    def test_no_manifest_permissions_added(self):
        m=(ROOT/'app/src/main/AndroidManifest.xml').read_text()
        self.assertEqual(m.count('<uses-permission'),1)
if __name__=='__main__':unittest.main(verbosity=2)
