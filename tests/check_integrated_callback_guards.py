"""Static checks of combined reviewed guards; does NOT execute Android callbacks."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ACT = (ROOT / 'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()

class IntegratedGuardChecks(unittest.TestCase):
    def test_completion_requires_current_player(self):
        block = ACT.split('player.setOnCompletionListener(mp->{',1)[1].split('player.setOnErrorListener',1)[0]
        self.assertIn('if(player!=mp)return;', block)

    def test_completion_checks_authorization_before_advancing(self):
        block = ACT.split('player.setOnCompletionListener(mp->{',1)[1].split('player.setOnErrorListener',1)[0]
        self.assertLess(block.index('CompletionPolicy.mayAdvance(playbackGate,audioFocusGate)'), block.index('CompletionPolicy.nextSelection('))
        self.assertLess(block.index('CompletionPolicy.mayAdvance(playbackGate,audioFocusGate)'), block.index('playFrom(next.playlist,next.index,false)'))

    def test_completion_no_focus_reacquisition(self):
        block = ACT.split('player.setOnCompletionListener(mp->{',1)[1].split('player.setOnErrorListener',1)[0]
        self.assertNotIn('requestAudioFocusForExplicitPlay',block)

    def test_error_listener_ignores_stale_player(self):
        block = ACT.split('player.setOnErrorListener((mp,what,extra)->{',1)[1].split('player.prepareAsync()',1)[0]
        self.assertLess(block.index('if(player!=mp)return true;'),block.index('stopPlayer();'))

    def test_late_prepare_preserves_navigation(self):
        block = ACT.split('player.setOnPreparedListener(',1)[1].split('player.setOnCompletionListener',1)[0]
        self.assertIn('if("NOW".equals(screen))showNow();',block)

    def test_stop_detaches_before_release(self):
        block = ACT.split('private boolean stopPlayer()',1)[1].split('private boolean persist()',1)[0]
        self.assertLess(block.index('player=null;'),block.index('old.reset();'))

    def test_release_runs_even_after_reset_failure(self):
        block = ACT.split('private boolean stopPlayer()',1)[1].split('private boolean persist()',1)[0]
        self.assertIn('finally{try{old.release();}catch(Exception ignored){}}',block)

    def test_completion_policy_is_pure_java(self):
        policy=(ROOT/'app/src/main/java/org/roarin/kyocerakeypad/core/CompletionPolicy.java').read_text()
        self.assertIn('playback.canStart() && focus.canStart()',policy)
        self.assertNotIn('android.',policy)

if __name__=='__main__':
    unittest.main(verbosity=2)
