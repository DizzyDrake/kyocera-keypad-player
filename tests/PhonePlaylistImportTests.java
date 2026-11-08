import org.roarin.kyocerakeypad.core.*;
import java.io.IOException;
import java.util.*;

public final class PhonePlaylistImportTests {
  static int n=0;
  static void check(boolean condition,String what){if(!condition)throw new AssertionError(what);n++;}
  static void reject(Runnable r,String what){boolean failed=false;try{r.run();}catch(IllegalArgumentException e){failed=true;}check(failed,what);}
  static PlayerState base() {
    PlayerState s=new PlayerState();
    s.tracks.put("t1",new PlayerState.Track("t1","content://media/1","one","a","b","Music",5000,12));
    s.tracks.put("t2",new PlayerState.Track("t2","content://media/2","two","a","b","Music",5000,12));
    s.createPlaylist("p1","Old",false);s.add("p1","t1");s.select(false,"p1","t1",1000);
    s.addBookmark("t1","Marked",700);
    return s;
  }
  static PhonePlaylistImport.Spec spec(String id,String name,String...keys){
    return new PhonePlaylistImport.Spec(id,name,false,Arrays.asList(keys));
  }
  public static void main(String[] args)throws Exception{
    PlayerState s=base();byte[] before=StateCodec.encode(s);
    List<PhonePlaylistImport.Spec> good=Arrays.asList(spec("pc1","Imported","t2","t1"));
    PlayerState saved=StateMutation.prepareAndSave(s, next->PhonePlaylistImport.apply(next,good),raw->true);
    check(saved!=s,"new durable-state candidate");
    check(Arrays.equals(before,StateCodec.encode(s)),"original not mutated");
    check(saved.playlists.size()==1 && saved.playlists.containsKey("pc1"),"all old playlists replaced");
    check(saved.getPlaylist("pc1").entries.equals(Arrays.asList("t2","t1")),"PC order retained");
    check(saved.music.playlistId.isEmpty() && saved.music.positionMs==0,"listening position reset");
    check(saved.book.playlistId.isEmpty() && saved.book.positionMs==0,"book position reset");
    PlayerState preserved=StateMutation.prepareAndSave(s,next->PhonePlaylistImport.apply(next,
         Arrays.asList(spec("p1","Retained","t2","t1"))),raw->true);
    check(preserved.music.playlistId.equals("p1") && preserved.music.positionMs==1000,
          "valid listening position preserved");
    check(saved.bookmarks.size()==1 && saved.bookmarks.get(0).positionMs==700,"bookmark preserved");
    check(saved.tracks.size()==2,"track metadata preserved");
    PlayerState declined=StateMutation.prepareAndSave(s,next->PhonePlaylistImport.apply(next,good),raw->false);
    check(declined==s && Arrays.equals(StateCodec.encode(s),before),"failed persistence retains exact original");
    reject(()->PhonePlaylistImport.apply(s,Arrays.asList(spec("x","OK","missing"))),"unknown phone track rejected");
    reject(()->PhonePlaylistImport.apply(s,Arrays.asList(spec("x","OK","t1","t1"))),"duplicate track rejected");
    reject(()->PhonePlaylistImport.apply(s,Arrays.asList(spec("x","Dup","t1"),spec("y","dup","t2"))),"duplicate name case-insensitive");
    reject(()->PhonePlaylistImport.apply(s,Arrays.asList(spec("x","A","t1"),spec("x","B","t2"))),"duplicate id rejected");
    reject(()->PhonePlaylistImport.apply(s,Arrays.asList(spec("x","Bad\nname","t1"))),"control character rejected");
    reject(()->PhonePlaylistImport.apply(s,null),"null list rejected");
    check(Arrays.equals(StateCodec.encode(s),before),"invalid imports did not mutate original");
    System.out.println("PhonePlaylistImport PASS "+n+" assertions (pure Java; no Android UI/ADB test)");
  }
}
