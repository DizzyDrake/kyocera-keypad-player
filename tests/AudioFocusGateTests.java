import org.roarin.kyocerakeypad.core.AudioFocusGate;
import org.roarin.kyocerakeypad.core.PlaybackGate;
import org.roarin.kyocerakeypad.core.PlayerState;

/** No Android framework: state-machine and fictional playback-position tests. */
public final class AudioFocusGateTests {
    private static int n;
    private static void yes(boolean ok,String why){n++;if(!ok)throw new AssertionError(why);}
    public static void main(String[] args){
        AudioFocusGate focus=new AudioFocusGate();
        PlaybackGate life=new PlaybackGate();
        yes(!focus.canStart(),"initial focus absent");
        focus.onGain();yes(!focus.canStart(),"unsolicited gain cannot start");
        focus.onExplicitRequest(false);yes(!focus.canStart(),"focus denial blocks playback");
        life.onResume();life.requestPlay();
        yes(life.canStart()&&!focus.canStart(),"foreground alone does not override denial");
        focus.onExplicitRequest(true);yes(life.canStart()&&focus.canStart(),"explicit focus grant allows play");
        focus.onLoss();life.requestPause();
        yes(!focus.canStart()&&!life.canStart(),"incoming call/focus loss blocks playback");
        focus.onGain();yes(!focus.canStart(),"focus return does not auto resume");
        life.requestPlay();yes(!focus.canStart(),"manual play without new focus grant blocked");
        focus.onExplicitRequest(false);yes(!focus.canStart(),"manual play during call denied");
        focus.onExplicitRequest(true);yes(focus.canStart()&&life.canStart(),"new explicit grant after call");
        focus.onAbandon();yes(!focus.canStart(),"manual pause releases focus");
        focus.onGain();yes(!focus.canStart(),"late gain after abandon ignored");
        life.onPause();yes(!life.canStart(),"background lifecycle pause blocks play");
        life.onResume();yes(!life.canStart(),"foreground restoration requires user Play");

        PlayerState state=new PlayerState();
        state.tracks.put("song",new PlayerState.Track("song","content://song","Song","A","B","C",900000,100));
        state.tracks.put("book",new PlayerState.Track("book","content://book","Book","A","B","C",3600000,200));
        state.createPlaylist("musiclist","Music",false);
        state.createPlaylist("booklist","Audiobook",true);
        state.add("musiclist","song");state.add("booklist","book");
        state.select(false,"musiclist","song",40000);
        state.select(true,"booklist","book",123456);
        state.addBookmark("book","chapter",123456);
        // Focus loss is not a playlist mutation; Activity pauses, snapshots and persists.
        focus.onExplicitRequest(true);focus.onLoss();
        yes(state.music.positionMs==40000,"music timestamp retained");
        yes(state.book.positionMs==123456,"audiobook timestamp retained");
        yes(state.bookmarks.size()==1&&state.bookmarks.get(0).positionMs==123456,"bookmark retained");
        yes(state.music.playlistId.equals("musiclist")&&state.book.playlistId.equals("booklist"),"separate playlists retained");
        System.out.println("PASS "+n+" audio focus gate and fictional state assertions (pure Java; Android uncompiled)");
    }
}
