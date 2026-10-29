"""Independent source-bound regression tests, NOT Android compilation/runtime proof."""
import os,re,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ORIGINAL=ROOT.parent/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java'
SOURCE=Path(os.environ.get('WQE082_ACTIVITY',str(ORIGINAL)))
text=SOURCE.read_text()
def between(a,b):
    assert text.count(a)==1,(a,text.count(a))
    return text.split(a,1)[1].split(b,1)[0]
class SourceReview(unittest.TestCase):
    def test_original_source_selection_is_persisted_before_media_open(self):
        s=between('private void playFrom(PlayerState.Playlist p,int index,boolean resume){','private void showNow(){')
        self.assertLess(s.index('state.select('),s.index('player.setDataSource('))
        self.assertLess(s.index('if(!persist())'),s.index('player.setDataSource('))
    def test_sync_media_open_failure_restores_previous_progress(self):
        s=between('private void playFrom(PlayerState.Playlist p,int index,boolean resume){','private void restoreUnstartedSelection(')
        catch=s.rsplit('}catch(Exception e)',1)[-1]
        self.assertIn('restoreUnstartedSelection(p.audiobook,p.id,key,previousProgress,previousActiveBook)',catch)
        self.assertLess(catch.index('stopPlayer()'),catch.index('restoreUnstartedSelection('))
    def test_prepared_failure_callback_restores_before_prepared_only(self):
        s=between('player.setOnErrorListener((mp,what,extra)->{','player.prepareAsync();showNow();')
        self.assertIn('if(player!=mp)return true;',s)
        self.assertIn('boolean failedBeforePrepared=!prepared;',s)
        self.assertIn('if(failedBeforePrepared)restoreUnstartedSelection(p.audiobook,p.id,key,previousProgress,previousActiveBook)',s)
    def test_restore_is_explicitly_persisted_and_failed_restore_warns(self):
        s=between('private void restoreUnstartedSelection(','private void showNow(){')
        # WQA359 strengthens the old unconditional restore: it validates the
        # pending context and durably saves a copy before publishing it.
        self.assertIn('FailedOpenRollback.attempt(',s)
        self.assertIn('if(rollback.restored())',s)
        self.assertIn('state=rollback.state;',s)
        self.assertIn('activeBook=previousActiveBook;',s)
        self.assertNotIn('state.progress(book).restoreFrom(before);',s)
        self.assertIn('Outcome.SAVE_FAILED',s)
    def test_constructor_inside_catch_boundary(self):
        s=between('private void playFrom(PlayerState.Playlist p,int index,boolean resume){','private void showNow(){')
        self.assertRegex(s,r'player=null;prepared=false;\s*try\{\s*player=new MediaPlayer\(\);')
    def test_preview_remains_separate(self):
        s=between('private void startPreview(String key){','private void showPreview(){')
        self.assertIn('previewPlayer=audition;',s)
        self.assertNotIn('state.select(',s)
        self.assertIn('if(!stopPlayer())',s)
    def test_core_state_java_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            core=ROOT.parent/'app/src/main/java/org/roarin/kyocerakeypad/core'
            src=[str(p) for p in core.glob('*.java')]
            p=subprocess.run(['javac','--release','8','-d',d,*src,str(ROOT/'FailedOpenSelectionTests.java')],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            p=subprocess.run(['java','-cp',d,'FailedOpenSelectionTests'],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertIn('PASS 12 fictional',p.stdout)
if __name__=='__main__':unittest.main(verbosity=2)
