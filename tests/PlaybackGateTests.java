import org.roarin.kyocerakeypad.core.PlaybackGate;

/** Offline pure-Java lifecycle regression probes, not an Android runtime test. */
public final class PlaybackGateTests {
    private static int assertions=0;
    private static void yes(boolean value,String description){assertions++;if(!value)throw new AssertionError(description);}
    public static void main(String[] args){
        PlaybackGate g=new PlaybackGate();
        yes(!g.canStart(),"no autoplay before Activity resumes");
        g.requestPlay();yes(!g.canStart(),"background request refused");
        g.onResume();yes(!g.canStart(),"resume does not create playback request");
        g.requestPlay();yes(g.canStart(),"explicit foreground play can start");
        g.onPause();yes(!g.canStart(),"onPause blocks delayed onPrepared and seek-complete callbacks");
        g.onResume();yes(!g.canStart(),"returning foreground does not autoplay");
        g.requestPlay();yes(g.canStart(),"user can explicitly resume after return");
        g.requestPause();yes(!g.canStart(),"manual pause blocks subsequent seek-complete callback");
        g.requestPlay();yes(g.canStart(),"manual play resumes");
        g.requestPause();yes(!g.canStart(),"navigation home stops playback authorization");
        System.out.println("PASS "+assertions+" playback gate assertions (pure Java; Android uncompiled)");
    }
}
