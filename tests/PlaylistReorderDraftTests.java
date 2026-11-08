import org.roarin.kyocerakeypad.core.*;
import java.util.*;
import java.io.*;

public final class PlaylistReorderDraftTests {
    private static int checks=0;
    private static void yes(boolean condition,String message){checks++;if(!condition)throw new AssertionError(message);}
    private static void eq(Object got,Object want){yes(Objects.equals(got,want),"expected "+want+" got "+got);}
    private static void bad(Runnable fn){checks++;try{fn.run();throw new AssertionError("Expected error");}catch(IllegalArgumentException|IllegalStateException expected){}}
    private static PlayerState sample(){
        PlayerState p=new PlayerState();p.createPlaylist("p","Mixed",false);
        for(String key:new String[]{"z","a","m","b"}){
            p.tracks.put(key,new PlayerState.Track(key,"content://test/"+key,"same title","","","",50000,10));
            p.add("p",key);
        }
        p.select(false,"p","a",21000);
        return p;
    }
    public static void main(String[] args)throws Exception{
        PlayerState base=sample();
        PlaylistReorderDraft d=new PlaylistReorderDraft("p",base.getPlaylist("p").entries,"a");
        eq(d.selectedIndex(),1);eq(d.originalIndex(),1);yes(!d.changed(),"fresh unchanged");
        yes(d.moveBy(-1),"up");eq(d.snapshot(),Arrays.asList("a","z","m","b"));eq(d.selectedIndex(),0);
        yes(!d.moveBy(-1),"top boundary");yes(d.moveBy(1),"down");eq(d.selectedIndex(),1);
        yes(d.moveBottom(),"bottom");eq(d.selectedIndex(),3);yes(!d.moveBottom(),"bottom boundary");
        yes(d.moveTop(),"top");eq(d.selectedIndex(),0);eq(d.selectedKey(),"a");
        eq(base.getPlaylist("p").entries,Arrays.asList("z","a","m","b")); // staged only
        eq(base.music.positionMs,21000L);
        List<String> isolated=d.snapshot();isolated.clear();eq(d.size(),4);
        bad(()->d.moveBy(2));bad(()->new PlaylistReorderDraft("p",Arrays.asList("x","x"),"x"));
        bad(()->new PlaylistReorderDraft("p",Arrays.asList("x"),"missing"));
        // A failed AtomicFile writer never publishes candidate, and never changes original.
        PlayerState failed=StateMutation.prepareAndSave(base,d::apply,bytes->false);
        yes(failed==base,"failure returns original identity");
        eq(base.getPlaylist("p").entries,Arrays.asList("z","a","m","b"));
        PlayerState committed=StateMutation.prepareAndSave(base,d::apply,bytes->true);
        yes(committed!=base,"commit yields new state");
        eq(committed.getPlaylist("p").entries,Arrays.asList("a","z","m","b"));
        eq(committed.music.trackKey,"a");eq(committed.music.positionMs,21000L);
        eq(base.getPlaylist("p").entries,Arrays.asList("z","a","m","b"));
        // Source list changed after draft: must reject, not overwrite new contents.
        PlayerState stale=sample();stale.getPlaylist("p").entries.remove("b");
        bad(()->d.apply(stale));
        eq(stale.getPlaylist("p").entries,Arrays.asList("z","a","m"));
        // Cancel simply discards the draft; re-entering sees unchanged saved order.
        PlaylistReorderDraft cancelled=new PlaylistReorderDraft("p",base.getPlaylist("p").entries,"m");
        cancelled.moveTop();eq(base.getPlaylist("p").entries,Arrays.asList("z","a","m","b"));
        // Reversing moves returns to unchanged; no unnecessary state write.
        PlaylistReorderDraft reverted=new PlaylistReorderDraft("p",base.getPlaylist("p").entries,"z");
        reverted.moveBottom();reverted.moveTop();yes(!reverted.changed(),"reverted unchanged");
        System.out.println("PlaylistReorderDraftTests "+checks+"/"+checks+" PASS");
    }
}
