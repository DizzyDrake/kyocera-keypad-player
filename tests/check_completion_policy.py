"""Static integration assertion: Android Activity is not compiled or executed."""
import sys
from pathlib import Path
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path.cwd()
s=(root/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
start=s.index('player.setOnCompletionListener(mp->{')
end=s.index('player.setOnErrorListener',start)
block=s[start:end]
needle='CompletionPolicy.mayAdvance(playbackGate,audioFocusGate)'
assert needle in block, 'Completion callback lacks an explicit playback/focus authorization guard'
assert block.index(needle)<block.index('CompletionPolicy.nextSelection('), 'Guard must precede current-state next-track selection'
assert block.index(needle)<block.index('playFrom(next.playlist,next.index,false)'), 'Guard must precede automatic next-track playback'
assert 'requestAudioFocusForExplicitPlay' not in block, 'Completion callback must not request new focus itself'
assert 'state.nextIndex(p.id,key)' not in block, 'Stale playlist/index mixing must be absent'
assert 'if(player!=mp)return;' in block, 'Stale MediaPlayer identity guard must remain'
print('PASS static completion guard appears before next-track transition; no Android runtime exercised')
