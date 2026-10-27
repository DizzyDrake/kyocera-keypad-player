import org.roarin.kyocerakeypad.core.AudioFocusGate;
import org.roarin.kyocerakeypad.core.PlaybackGate;
import org.roarin.kyocerakeypad.core.CompletionPolicy;
import org.roarin.kyocerakeypad.core.PlayerState;

/** Pure Java event-sequence model; does NOT execute Android MediaPlayer callbacks. */
public final class CompletionPolicyTests {
    private static int assertions;
    private static void check(boolean b,String msg) {
        assertions++;
        if(!b) throw new AssertionError(msg);
    }
    public static void main(String[] args) {
        PlaybackGate playback=new PlaybackGate();
        AudioFocusGate focus=new AudioFocusGate();
        check(!CompletionPolicy.mayAdvance(playback,focus),"no implicit startup");
        playback.onResume();
        check(!CompletionPolicy.mayAdvance(playback,focus),"foreground alone insufficient");
        playback.requestPlay();
        check(!CompletionPolicy.mayAdvance(playback,focus),"explicit play without focus insufficient");
        focus.onExplicitRequest(false);
        check(!CompletionPolicy.mayAdvance(playback,focus),"denied focus");
        focus.onExplicitRequest(true);
        check(CompletionPolicy.mayAdvance(playback,focus),"normal authorized track completion may advance");
        focus.onLoss();
        playback.requestPause();
        check(!CompletionPolicy.mayAdvance(playback,focus),"call focus loss must suppress late completion");
        focus.onGain();
        check(!CompletionPolicy.mayAdvance(playback,focus),"focus gain must not auto advance");
        playback.requestPlay();
        check(!CompletionPolicy.mayAdvance(playback,focus),"Play without new grant insufficient");
        focus.onExplicitRequest(true);
        check(CompletionPolicy.mayAdvance(playback,focus),"fresh explicit grant permits continuation");
        playback.requestPause();
        check(!CompletionPolicy.mayAdvance(playback,focus),"manual pause suppresses late completion");
        playback.requestPlay();
        playback.onPause();
        check(!CompletionPolicy.mayAdvance(playback,focus),"background pause suppresses completion");
        playback.onResume();
        check(!CompletionPolicy.mayAdvance(playback,focus),"resume alone does not advance");
        playback.requestPlay();
        check(CompletionPolicy.mayAdvance(playback,focus),"fresh Play in foreground with focus");
        focus.onAbandon();
        check(!CompletionPolicy.mayAdvance(playback,focus),"abandon suppresses completion");
        focus.onGain();
        check(!CompletionPolicy.mayAdvance(playback,focus),"stale focus gain cannot authorize completion");

        PlayerState state=new PlayerState();
        state.tracks.put("music",new PlayerState.Track("music","content://music","Music","A","B","C",100000,1));
        state.tracks.put("book",new PlayerState.Track("book","content://book","Book","A","B","C",500000,2));
        state.createPlaylist("musiclist","Music",false);
        state.createPlaylist("booklist","Book",true);
        state.add("musiclist","music");state.add("booklist","book");
        state.select(false,"musiclist","music",42000);
        state.select(true,"booklist","book",123000);
        check(state.music.positionMs==42000,"music progress remains unchanged by policy");
        check(state.book.positionMs==123000,"book progress remains unchanged by policy");
        System.out.println("PASS "+assertions+" completion-policy assertions (pure Java; no Android execution)");
    }
}
