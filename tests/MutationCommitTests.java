import java.io.IOException;
import java.util.*;
import java.util.function.Consumer;
import org.roarin.kyocerakeypad.core.*;

/** Fictional pure-Java transaction tests. No Android AtomicFile, APK or real media. */
public final class MutationCommitTests {
    private static int assertions=0;
    private static void ok(boolean yes,String msg){assertions++;if(!yes)throw new AssertionError(msg);}
    private static PlayerState fixture(){
        PlayerState s=new PlayerState();
        s.tracks.put("t1",new PlayerState.Track("t1","content://fake/1","Song A","","","",120000,100));
        s.tracks.put("t2",new PlayerState.Track("t2","content://fake/2","Song B","","","",120000,100));
        s.tracks.put("t3",new PlayerState.Track("t3","content://fake/3","Book C","","","",300000,100));
        s.createPlaylist("music","Original music",false);s.add("music","t1");s.add("music","t2");
        s.createPlaylist("book","Original book",true);s.add("book","t3");
        s.select(false,"music","t1",42000);s.select(true,"book","t3",72000);
        s.addBookmark("t3","Chapter",60000);
        return s;
    }
    private static void checkMutation(String label,Consumer<PlayerState> change) throws Exception {
        PlayerState original=fixture();
        byte[] before=StateCodec.encode(original);
        final int[] writes={0};
        PlayerState rejected=StateMutation.prepareAndSave(original,change,bytes->{writes[0]++;return false;});
        ok(rejected==original,label+" returned original on failed write");
        ok(Arrays.equals(before,StateCodec.encode(original)),label+" original bytes intact");
        ok(writes[0]==1,label+" attempted one write");
        final byte[][] saved={null};
        PlayerState accepted=StateMutation.prepareAndSave(original,change,bytes->{saved[0]=bytes.clone();return true;});
        ok(accepted!=original,label+" publishes a new state only after success");
        ok(Arrays.equals(saved[0],StateCodec.encode(accepted)),label+" exact committed bytes");
        ok(Arrays.equals(before,StateCodec.encode(original)),label+" original unchanged after success");
        ok(!Arrays.equals(before,saved[0]),label+" meaningful state change");
        ok(accepted.book.positionMs==72000,label+" unrelated audiobook progress preserved");
        ok(accepted.music.positionMs==("delete playlist".equals(label)?0:42000),label+" music progress follows mutation semantics");
    }
    public static void main(String[] args)throws Exception {
        checkMutation("create playlist",s->s.createPlaylist("new","New",false));
        checkMutation("rename playlist",s->s.renamePlaylist("music","Changed"));
        checkMutation("delete playlist",s->s.deletePlaylist("music"));
        checkMutation("move up",s->s.move("music",1,0));
        checkMutation("move down",s->s.move("music",0,1));
        checkMutation("remove track",s->s.remove("music",0));
        checkMutation("add bookmark",s->s.addBookmark("t3","Second",90000));
        checkMutation("rename bookmark",s->s.renameBookmark(0,"Renamed"));
        checkMutation("delete bookmark",s->s.deleteBookmark(0));
        PlayerState original=fixture();byte[] before=StateCodec.encode(original);
        final int[] writes={0};
        try{
            StateMutation.prepareAndSave(original,s->{s.renamePlaylist("music","partial");throw new IllegalArgumentException("synthetic failure");},bytes->{writes[0]++;return true;});
            throw new AssertionError("Mutation exception expected");
        }catch(IllegalArgumentException expected){}
        ok(writes[0]==0,"throwing mutation cannot reach writer");
        ok(Arrays.equals(before,StateCodec.encode(original)),"throwing mutation leaves original intact");
        try{
            StateMutation.prepareAndSave(original,s->s.renamePlaylist("music","new"),bytes->{throw new IOException("synthetic storage failure");});
            throw new AssertionError("Storage exception expected");
        }catch(IOException expected){}
        ok(Arrays.equals(before,StateCodec.encode(original)),"throwing writer leaves original intact");
        System.out.println("PASS "+assertions+" mutation commit assertions (fictional pure Java)");
    }
}
