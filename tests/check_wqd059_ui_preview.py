"""Source contract checks for WQD059, not Android compilation or hardware tests."""
from pathlib import Path
import re,unittest
root=Path(__file__).resolve().parents[1]
a=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
g=(root/'app/build.gradle').read_text()

def section(start,end):
    assert a.count(start)==1,(start,a.count(start))
    return a.split(start,1)[1].split(end,1)[0]

class WQD059Preview(unittest.TestCase):
    def test_library_select_opens_actions_not_auto_play(self):
        s=section('private void showLibrary(boolean book){','/** Source-only keypad mapping;')
        self.assertIn('showLibraryTrackActions(t.key)',s)
        self.assertIn('▶ Preview / Play (no playlist change)',s)
        self.assertIn('Choose playlist to add',s)
        self.assertNotIn('To play, add this track',s)
    def test_preview_uses_separate_player(self):
        self.assertIn('private MediaPlayer previewPlayer;',a)
        s=section('private void startPreview(String key){','private void showPreview(){')
        self.assertIn('new MediaPlayer()',s)
        self.assertIn('previewPlayer=audition',s)
        self.assertIn('stopPlayer()',s)
        self.assertIn('if(!stopPlayer())',s)
        self.assertIn('if(!requestAudioFocusForExplicitPlay(false))',s)
        self.assertIn('if(previewPlayer!=mp)return',s)
        self.assertIn('if(previewRequested && audioFocusGate.canStart())mp.start()',s)
        for forbidden in ['state.select(', 'state.savePosition(', 'state.addBookmark(', 'state.add(', 'state.progress(']:
            self.assertNotIn(forbidden,s)
    def test_preview_cannot_autoresume_after_focus_loss(self):
        s=section('private void onAudioFocusChanged(int change){','private void abandonAudioFocus(){')
        self.assertIn('previewRequested=false;',s)
        self.assertIn('previewPlayer.pause()',s)
        self.assertIn('audioFocusGate.onLoss()',s)
        self.assertNotIn('previewPlayer.start()',s)
    def test_preview_cleanup_and_back(self):
        s=section('private void stopPreview(){','/** Source-only keypad mapping;')
        self.assertLess(s.index('previewPlayer=null;'),s.index('old.reset()'))
        self.assertIn('old.release()',s)
        self.assertIn('if(hadPreview)abandonAudioFocus()',s)
        self.assertIn('case "PREVIEW":returnFromPreview();break;',a)
        self.assertIn('onPause(){stopPreview();pauseForNavigation()',a)
        self.assertIn('onDestroy(){timer.removeCallbacks(tick);stopPreview();stopPlayer()',a)
    def test_preview_does_not_mutate_playlist_or_progress(self):
        s=section('private void startPreview(String key){','/** Source-only keypad mapping;')
        # Only explicit add helper may mutate a playlist, not preview actions.
        self.assertNotIn('state.select(',s)
        self.assertNotIn('state.savePosition(',s)
        self.assertNotIn('state.addBookmark(',s)
    def test_add_rollback_on_persist_failure(self):
        s=section('private boolean addTrackAndPersist(String playlistId,String key){','private void choosePlaylistForLibraryTrack(String key){')
        self.assertIn('missing.contains(key) || conflicts.contains(key)',s)
        self.assertIn('if(persist())return true;',s)
        self.assertIn('p.entries.remove(key)',s)
        self.assertIn('return false;',s)
    def test_persist_guards_and_alphabet(self):
        self.assertIn('state.progress(p.audiobook).restoreFrom(previousProgress)',a)
        self.assertIn('CompletionPolicy.mayAdvance(playbackGate,audioFocusGate)',a)
        self.assertIn('private void showAlphabetIndex()',a)
        self.assertIn('private void prompt(',a)
    def test_readable_color_and_size(self):
        for token in ['setTextSize(19)','setTextSize(18)','setTextSize(15)', '#713E46','#252022','#F5F0EB','#D6A6AD']:
            self.assertIn(token,a)
        self.assertIn('setMaxLines(4)',a)
    def test_about_is_truthful_source_only(self):
        for token in ['About / version','Build configured UTC: ','Source prepared: 2026-10-27','Release date: Not released','Made by GPT-6 and Aurora Williamsen']:
            self.assertIn(token,a)
        self.assertIn("buildConfigField 'String', 'BUILD_UTC'",g)
        self.assertIn('TimeZone.getTimeZone(\'UTC\')',g)
        self.assertIn("versionName '0.1.7-source-review'",g)
        self.assertNotIn('APK built UTC:',a)
    def test_only_original_permission(self):
        manifest=(root/'app/src/main/AndroidManifest.xml').read_text()
        self.assertEqual(manifest.count('<uses-permission'),1)
        self.assertIn('READ_EXTERNAL_STORAGE',manifest)
        self.assertNotIn('INTERNET',manifest)

if __name__=='__main__':unittest.main(verbosity=2)
