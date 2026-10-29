"""Source-level Android wiring checks; NOT Android compilation or device behavior."""
from pathlib import Path
import re,unittest
A=Path(__file__).resolve().parents[1]/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java'
s=A.read_text()
class Wiring(unittest.TestCase):
    def test_nine_paths_use_transaction(self):
        for name in ['Create playlist','Rename playlist','Delete playlist','Move track up','Move track down','Remove track','Add bookmark','Rename bookmark','Delete bookmark']:
            self.assertEqual(s.count('commitMutation("'+name+'"'),1,name)
    def test_only_publish_after_durable_save(self):
        section=s.split('private boolean commitMutation(',1)[1].split('private boolean writeStateBytes(',1)[0]
        self.assertIn('StateMutation.prepareAndSave(state,edit,this::writeStateBytes)',section)
        self.assertLess(section.index('if(next==state)'),section.index('state=next;'))
        self.assertIn('state=next;',section)
    def test_delete_does_not_proceed_after_failed_stop(self):
        section=s.split('item("Delete playlist",',1)[1].split('int i=0;',1)[0]
        self.assertIn('if(!stopPlayer())',section)
        self.assertIn('commitMutation("Delete playlist"',section)
    def test_failed_open_peer_merged(self):
        self.assertIn('restoreUnstartedSelection(p.audiobook,p.id,key,previousProgress,previousActiveBook)',s)
        self.assertIn('FailedOpenRollback.attempt(',s)
        self.assertIn('boolean failedBeforePrepared=!prepared',s)
    def test_no_extra_permission(self):
        manifest=(A.parents[4]/'AndroidManifest.xml') if False else A.parents[2]/'AndroidManifest.xml'
        # Source file path is .../main/java/...; check the actual manifest by project root.
        root=Path(__file__).resolve().parents[1]
        m=(root/'app/src/main/AndroidManifest.xml').read_text()
        self.assertEqual(m.count('<uses-permission'),1)
        self.assertNotIn('INTERNET',m)
if __name__=='__main__':unittest.main(verbosity=2)
