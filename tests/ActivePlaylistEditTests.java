import java.util.*;
import org.roarin.kyocerakeypad.core.*;

/** Synthetic tests; no device, Android OS or audio files. */
public final class ActivePlaylistEditTests {
    static int checks=0;
    static void eq(Object actual,Object expected,String label){checks++;
        if(!Objects.equals(actual,expected))throw new AssertionError(label+": expected "+expected+", got "+actual);}
    static void yes(boolean value,String label){checks++;if(!value)throw new AssertionError(label);}
    static void fails(Runnable operation,String label){checks++;
        try{operation.run();}catch(IllegalArgumentException expected){return;}
        throw new AssertionError("accepted invalid: "+label);
    }
    public static void main(String[] args) throws Exception {
        List<String> original=Arrays.asList("a","b","c","d");
        eq(PlaylistRemovalPolicy.successor(original,null,"b",false),"c","next in saved order");
        eq(PlaylistRemovalPolicy.successor(original,null,"d",false),null,"last stops if repeat off");
        eq(PlaylistRemovalPolicy.successor(original,null,"d",true),"a","last wraps if repeat playlist");
        eq(PlaylistRemovalPolicy.successor(original,null,"a",false),"b","first gets next");
        eq(PlaylistRemovalPolicy.successor(Collections.singletonList("a"),null,"a",true),null,"last singleton stops even if repeat");
        eq(PlaylistRemovalPolicy.successor(original,Arrays.asList("b","d","a","c"),"b",false),"d","shuffle order next");
        eq(PlaylistRemovalPolicy.successor(original,Arrays.asList("b","d","a","c"),"c",true),"b","shuffle order wrap");
        eq(PlaylistRemovalPolicy.successor(original,Arrays.asList("x","d","a","c"),"b",false),"c","bad shuffle falls back to saved");
        eq(PlaylistRemovalPolicy.successor(original,Arrays.asList("b","b","a","d"),"b",false),"c","duplicate shuffle invalid");
        eq(PlaylistRemovalPolicy.savedSuccessor(original,"d"),"a","inactive session picks next saved item");
        fails(()->PlaylistRemovalPolicy.successor(original,null,"unknown",false),"unknown current");
        fails(()->PlaylistRemovalPolicy.successor(null,null,"b",false),"null saved");
        eq(original,Arrays.asList("a","b","c","d"),"source not mutated");

        PlaylistPlaybackOrder order=new PlaylistPlaybackOrder();
        order.start("list",original,"b",true,new Random(11));
        List<String> shuffled=order.snapshot();
        order.removeEntry("other","a");
        eq(order.snapshot(),shuffled,"unrelated playlist removal ignored");
        order.removeEntry("list","c");
        List<String> copy=order.snapshot();
        yes(!copy.contains("c"),"removed entry absent");
        yes(copy.size()==3,"three remain");
        yes(order.matches("list",Arrays.asList("a","b","d"),"b"),"remaining session matches saved");
        order.removeEntry("list","missing");
        eq(order.snapshot(),copy,"unknown entry no-op");
        order.start("book",Arrays.asList("bk1","bk2"),"bk1",false,new Random(2));
        eq(order.snapshot(),Arrays.asList("bk1","bk2"),"book saved order preserved");

        PlayerState state=new PlayerState();
        for(String k:original)state.tracks.put(k,new PlayerState.Track(k,"content://"+k,k,"","","",15000L,12L));
        PlayerState.Playlist list=state.createPlaylist("pl","Music",false);
        list.entries.addAll(original);
        state.select(false,"pl","b",4000L);
        PlayerState old=state;
        PlayerState failure=StateMutation.prepareAndSave(old,next->{
            next.remove("pl",1);
            next.select(false,"pl","c",0L);
        },bytes->false);
        yes(failure==old,"failed write preserves original object");
        eq(old.music.trackKey,"b","failed write leaves current track");
        eq(old.getPlaylist("pl").entries,original,"failed write preserves saved playlist");
        PlayerState saved=StateMutation.prepareAndSave(old,next->{
            next.remove("pl",1);next.select(false,"pl","c",0L);
        },bytes->true);
        eq(saved.music.trackKey,"c","successful removal selects successor");
        eq(saved.music.positionMs,0L,"new track progress resets");
        eq(saved.getPlaylist("pl").entries,Arrays.asList("a","c","d"),"only one entry removed");
        yes(saved.tracks.containsKey("b"),"removal does not delete audio identity");
        yes(old.getPlaylist("pl").entries.equals(original),"original immutable before commit");
        System.out.println("PASS "+checks+" active-playlist plan and durable mutation checks");
    }
}
