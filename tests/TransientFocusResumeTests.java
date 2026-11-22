import org.roarin.kyocerakeypad.core.AudioFocusGate;
import org.roarin.kyocerakeypad.core.PlaybackGate;
import org.roarin.kyocerakeypad.core.PlayerState;
/** DEV17: Android-free logic for both lanes; real focus callbacks still need device tests. */
public final class TransientFocusResumeTests {
    private static int n;
    private static void check(boolean c,String why){ n++; if(!c)throw new AssertionError(why); }
    private static void verifyLane(boolean book){
        AudioFocusGate f=new AudioFocusGate(); PlaybackGate g=new PlaybackGate();
        g.onResume();g.requestPlay(); f.onExplicitRequest(true);
        check(f.canStart()&&g.canStart(),"initial explicit play");
        f.onTransientLoss();g.requestPause();
        check(!f.canStart()&&!g.canStart(),"transient loss must pause");
        f.onGain();g.requestPlay();
        check(f.canStart()&&g.canStart(),"transient gain may resume previously requested "+book);
        // Manual Pause while focus temporarily absent clears both policies.
        f.onTransientLoss();g.requestPause();f.onAbandon();
        f.onGain();g.requestPlay();check(!f.canStart(),"manual Pause cannot autoresume");
        // Permanent loss/call cannot resume without a fresh explicit request.
        f.onExplicitRequest(true);f.onLoss();f.onGain();
        check(!f.canStart(),"permanent loss cannot autoplay");
        f.onExplicitRequest(true);check(f.canStart(),"fresh user grant can play");
        f.onAbandon();f.onGain();check(!f.canStart(),"no unsolicited autoplay");
    }
    public static void main(String[] args){
        verifyLane(false);verifyLane(true);
        AudioFocusGate f=new AudioFocusGate();f.onTransientLoss();f.onGain();
        check(!f.canStart(),"unsolicited gain cannot start without an active focus request");
        PlayerState s=new PlayerState();
        s.tracks.put("song",new PlayerState.Track("song","content://song","Song","A","B","C",60000,123));
        s.tracks.put("chapter",new PlayerState.Track("chapter","content://chapter","Chapter","A","B","C",120000,456));
        s.createPlaylist("music","Music",false);s.createPlaylist("audiobooks","Books",true);
        s.add("music","song");s.add("audiobooks","chapter");
        s.select(false,"music","song",42000); s.select(true,"audiobooks","chapter",72000);
        check(s.music.positionMs==42000 && s.book.positionMs==72000,"distinct music and book positions unchanged");
        System.out.println("PASS "+n+" transient focus / both-lane source-state checks (host-only)");
    }
}
