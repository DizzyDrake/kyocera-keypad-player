#!/usr/bin/env python3
"""Service-aware source regression checks, not Android lifecycle execution.
The inherited Activity guards and their failure logs are retained separately.
"""
from pathlib import Path
import unittest
root=Path(__file__).resolve().parents[1]
s=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlaybackService.java').read_text()
a=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
m=(root/'app/src/main/AndroidManifest.xml').read_text()
def between(start,end): return s.split(start,1)[1].split(end,1)[0]
class ServiceLifecycleSource(unittest.TestCase):
 def test_late_foreground_start_is_promoted_then_reconciled(self):
  b=between('int onStartCommand(', 'private static MediaTransportSequencer.Key')
  self.assertLess(b.index('showForeground();'),b.index('retireForeground();'))
  self.assertIn('player == null || !playbackGate.canStart()',b)
  self.assertIn('START_NOT_STICKY',b)
 def test_stop_detaches_before_release_and_retires(self):
  b=between('boolean stopPlayer(){','void pause(){')
  self.assertLess(b.index('player=null'),b.index('old.release()'))
  self.assertIn('retireForeground()',b)
 def test_manual_start_failure_releases_player(self):
  b=between('void explicitPlay(){','void toggle(){')
  self.assertIn('player.start()',b)
  self.assertIn('stopPlayer();error("Playback could not resume")',b)
 def test_pause_failure_releases_and_success_saves(self):
  b=between('void pause(){','void explicitPlay(){')
  for text in ['playbackGate.requestPause()', 'stopPlayer();error(', 'savePosition()', 'persist()', 'retireForeground()']: self.assertIn(text,b)
 def test_focus_loss_latches_and_gain_never_plays(self):
  b=between('private void focusChanged(', 'void abandonFocus(){')
  self.assertIn('AUDIOFOCUS_GAIN){focusGate.onGain();return;}',b)
  for text in ['focusGate.onLoss()', 'playbackGate.requestPause()', 'savePosition()', 'persist()', 'retireForeground()']: self.assertIn(text,b)
 def test_callbacks_are_bound_to_current_player(self):
  b=between('mp.setOnPreparedListener(', 'mp.prepareAsync();')
  for text in ['if(player!=ready)return;', 'if(player!=seeked)return;', 'if(player!=done', 'if(player!=failed)return true;', 'restoreFailedSelection(']: self.assertIn(text,b)
 def test_sleep_and_explicit_home_are_distinct(self):
  b=a.split('@Override public void onPause(){',1)[1].split('@Override public void onDestroy(){',1)[0]
  self.assertNotIn('pauseForNavigation()',b)
  self.assertIn('case "NOW":showHome();break;',a)
  self.assertIn('Main menu (keeps playing)',a)
  self.assertIn('android.permission.WAKE_LOCK',m)
 def test_now_playing_refresh_preserves_selection(self):
  b=a.split('@Override public void onPlaybackChanged(){',1)[1].split('@Override public void onPlaybackError',1)[0]
  self.assertIn('list.getSelectedItemPosition()',b)
  self.assertIn('list.setSelection(selected)',b)
 def test_media_buttons_and_no_double_seek(self):
  for key in ['KEYCODE_MEDIA_PLAY_PAUSE','KEYCODE_MEDIA_NEXT','KEYCODE_MEDIA_PREVIOUS']: self.assertIn(key,s)
  self.assertNotIn('transport.setDoubleSeekEnabled(true)',s)
if __name__=='__main__': unittest.main(verbosity=2)
