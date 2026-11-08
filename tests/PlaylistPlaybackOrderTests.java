import java.util.*;
import org.roarin.kyocerakeypad.core.PlaylistPlaybackOrder;
import org.roarin.kyocerakeypad.core.MediaTransportSequencer;

public final class PlaylistPlaybackOrderTests {
    static int checks=0;
    static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
    public static void main(String[] args){
        List<String> saved=new ArrayList<>(Arrays.asList("A","B","C","D"));
        PlaylistPlaybackOrder order=new PlaylistPlaybackOrder();
        order.start("p",saved,"A",false,new Random(2));
        check(order.snapshot().equals(saved),"shuffle off retains stored order");
        check("B".equals(order.next("A",1,PlaylistPlaybackOrder.Repeat.OFF,true)),"off advances");
        check(order.next("D",1,PlaylistPlaybackOrder.Repeat.OFF,true)==null,"off stops at end");
        check("A".equals(order.next("D",1,PlaylistPlaybackOrder.Repeat.PLAYLIST,true)),"repeat playlist wraps");
        check("D".equals(order.next("D",1,PlaylistPlaybackOrder.Repeat.TRACK,true)),"repeat track on completion");
        check(order.next("D",1,PlaylistPlaybackOrder.Repeat.TRACK,false)==null,"manual NEXT bypasses repeat-track");
        check("A".equals(order.next("B",-1,PlaylistPlaybackOrder.Repeat.OFF,false)),"previous manual");
        order.start("p",saved,"C",false,new Random(2));
        check("D".equals(order.next("C",1,PlaylistPlaybackOrder.Repeat.OFF,true)),"selected track does not wrap in natural order");
        order.start("p",saved,"C",true,new Random(2));
        check("C".equals(order.snapshot().get(0)),"shuffle starts at selected track");
        check(new HashSet<>(order.snapshot()).equals(new HashSet<>(saved)),"shuffle preserves membership");
        check(saved.equals(Arrays.asList("A","B","C","D")),"saved playlist never reordered");
        check(order.matches("p",saved,"C"),"order matches source");
        check(!order.matches("other",saved,"C"),"playlist identity checked");
        check(!order.matches("p",Arrays.asList("A","B","C"),"C"),"stale order rejected");
        order.start("p",saved,"A",true,new Random(2));
        check(order.snapshot().size()==4,"shuffle size stable");
        MediaTransportSequencer t=new MediaTransportSequencer(350);
        check(t.onPress(MediaTransportSequencer.Key.NEXT,1000).contains(MediaTransportSequencer.Action.NEXT),"default next immediate");
        check(t.setDoubleSeekEnabled(true).isEmpty(),"enable clean");
        check(t.onPress(MediaTransportSequencer.Key.NEXT,2000).isEmpty(),"first next pending");
        check(t.flush(2200).isEmpty(),"not premature");
        check(t.onPress(MediaTransportSequencer.Key.NEXT,2250).contains(MediaTransportSequencer.Action.SEEK_FORWARD_10S),"double next seeks");
        check(t.onPress(MediaTransportSequencer.Key.NEXT,3000).isEmpty(),"new single pending");
        check(t.flush(3350).contains(MediaTransportSequencer.Action.NEXT),"single next fires after deadline");
        check(!t.hasPending(),"flush clears pending");
        System.out.println("PASS "+checks+" playlist and media-sequencer checks");
    }
}
