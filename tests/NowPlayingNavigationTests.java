import org.roarin.kyocerakeypad.core.NowPlayingNavigation;
import org.roarin.kyocerakeypad.core.PlayerState;
import java.util.*;
public final class NowPlayingNavigationTests {
    private static int checks=0;
    static void eq(Object actual,Object expected,String what){
        checks++;if(!Objects.equals(actual,expected))throw new AssertionError(what+" expected="+expected+" got="+actual);
    }
    public static void main(String[] args){
        List<String> saved=Arrays.asList("c","a","b");
        List<String> shuffled=Arrays.asList("a","b","c");
        NowPlayingNavigation.Neighbors n=NowPlayingNavigation.neighbors(saved,shuffled,"a",false,false);
        eq(n.previousKey,"c","saved previous");eq(n.nextKey,"b","saved next");
        eq(n.sessionShuffleOrder,false,"not shuffled");
        n=NowPlayingNavigation.neighbors(saved,shuffled,"a",true,false);
        eq(n.previousKey,null,"shuffle first previous");eq(n.nextKey,"b","shuffle next");
        eq(n.sessionShuffleOrder,true,"session shuffle label");
        n=NowPlayingNavigation.neighbors(saved,shuffled,"a",true,true);
        eq(n.previousKey,"c","shuffle wrap previous");eq(n.nextKey,"b","shuffle next with wrap");
        n=NowPlayingNavigation.neighbors(saved,Arrays.asList("a","b","other"),"a",true,false);
        eq(n.previousKey,null,"stale shuffle is unknown");
        eq(n.nextKey,null,"stale shuffle next is unknown");eq(n.sessionShuffleOrder,false,"stale shuffle not presented");
        n=NowPlayingNavigation.neighbors(saved,shuffled,"c",false,false);
        eq(n.previousKey,null,"first saved boundary");eq(n.nextKey,"a","first saved next");
        n=NowPlayingNavigation.neighbors(saved,shuffled,"b",false,false);
        eq(n.nextKey,null,"last saved boundary");
        n=NowPlayingNavigation.neighbors(saved,shuffled,"b",false,true);
        eq(n.nextKey,"c","repeat playlist wrap");
        n=NowPlayingNavigation.neighbors(saved,shuffled,"absent",true,true);
        eq(n.previousKey,null,"missing identity previous");eq(n.nextKey,null,"missing identity next");
        n=NowPlayingNavigation.neighbors(Arrays.asList("only"),Arrays.asList("only"),"only",true,true);
        eq(n.previousKey,null,"single track no self previous");eq(n.nextKey,null,"single track no self next");
        List<PlayerState.Bookmark> marks=Arrays.asList(
            new PlayerState.Bookmark("other","other",100),
            new PlayerState.Bookmark("x","later",500),
            new PlayerState.Bookmark("x","earlier",100),
            new PlayerState.Bookmark("x","same",300),
            new PlayerState.Bookmark("x","nearer",400));
        eq(NowPlayingNavigation.bookmarkIndex(marks,"x",300,-1),2,"earlier by time");
        eq(NowPlayingNavigation.bookmarkIndex(marks,"x",300,1),4,"later by time");
        eq(NowPlayingNavigation.bookmarkIndex(marks,"x",500,1),-1,"no later");
        eq(NowPlayingNavigation.bookmarkIndex(marks,"x",100,-1),-1,"no earlier");
        eq(NowPlayingNavigation.bookmarkIndex(marks,"other",50,1),0,"track isolation");
        eq(NowPlayingNavigation.bookmarkIndex(marks,"x",300,0),-1,"invalid direction");
        System.out.println(checks+"/"+checks+" Now Playing navigation checks PASS");
    }
}
