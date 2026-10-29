import org.roarin.kyocerakeypad.core.*;
import java.util.Arrays;

/** Fictional state-only tests: persist() is simulated, Android AtomicFile is NOT tested. */
public final class RollbackProgressTests {
    private static int checks=0;
    private static void ok(boolean value,String why){checks++;if(!value)throw new AssertionError(why);}
    private static PlayerState make(){
        PlayerState s=new PlayerState();
        s.tracks.put("m1",new PlayerState.Track("m1","content://fiction/m1","Music A","","","",180000,1));
        s.tracks.put("m2",new PlayerState.Track("m2","content://fiction/m2","Music B","","","",180000,1));
        s.tracks.put("b1",new PlayerState.Track("b1","content://fiction/b1","Book A","","","",900000,1));
        s.tracks.put("b2",new PlayerState.Track("b2","content://fiction/b2","Book B","","","",900000,1));
        s.createPlaylist("music","Music",false);s.add("music","m1");s.add("music","m2");
        s.createPlaylist("book","Book",true);s.add("book","b1");s.add("book","b2");
        s.select(false,"music","m1",40000);
        s.select(true,"book","b1",65000);
        s.addBookmark("b1","chapter",61000);
        return s;
    }
    private static void testFailure(boolean book) throws Exception {
        PlayerState s=make();
        byte[] durable=StateCodec.encode(s);
        PlayerState.Progress prior=new PlayerState.Progress(s.progress(book));
        PlayerState.Progress otherBefore=new PlayerState.Progress(s.progress(!book));
        s.select(book,book?"book":"music",book?"b2":"m2",0);
        // Simulate AtomicFile save failure: no new durable bytes are committed.
        s.progress(book).restoreFrom(prior);
        ok(Arrays.equals(StateCodec.encode(s),durable),"full state restored on failed initial save");
        ok(s.progress(book).trackKey.equals(book?"b1":"m1"),"old track restored");
        ok(s.progress(book).positionMs==(book?65000:40000),"old playhead restored");
        ok(s.progress(!book).trackKey.equals(otherBefore.trackKey),"other listening kind track unaffected");
        ok(s.progress(!book).positionMs==otherBefore.positionMs,"other listening kind time unaffected");
        ok(s.bookmarks.size()==1 && s.bookmarks.get(0).positionMs==61000,"bookmark unaffected");
        // A later unrelated successful save must not commit the unplayed selection.
        PlayerState later=StateCodec.decode(StateCodec.encode(s));
        ok(later.progress(book).trackKey.equals(prior.trackKey),"later persist keeps prior track");
        ok(later.progress(book).positionMs==prior.positionMs,"later persist keeps prior playhead");
    }
    private static void testSuccess(boolean book) throws Exception {
        PlayerState s=make();
        PlayerState.Progress before=new PlayerState.Progress(s.progress(book));
        s.select(book,book?"book":"music",book?"b2":"m2",12000);
        // Simulate a successful save: do not invoke rollback.
        PlayerState saved=StateCodec.decode(StateCodec.encode(s));
        ok(saved.progress(book).trackKey.equals(book?"b2":"m2"),"successful selection retained");
        ok(saved.progress(book).positionMs==12000,"successful position retained");
        ok(!s.progress(book).trackKey.equals(before.trackKey),"snapshot is independent of live selection");
    }
    public static void main(String[] args) throws Exception {
        testFailure(false);testFailure(true);testSuccess(false);testSuccess(true);
        System.out.println("PASS "+checks+" fictional rollback assertions (pure Java; no Android I/O)");
    }
}
