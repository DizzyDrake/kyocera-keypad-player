import org.roarin.kyocerakeypad.core.*;
import java.util.*;

public final class StalePlaylistImportTests {
    static int assertions=0;
    static void ok(boolean b,String label){if(!b) throw new AssertionError(label);assertions++;}
    static void reject(Runnable fn,String label){boolean failed=false;try{fn.run();}catch(IllegalArgumentException ex){failed=true;}ok(failed,label);}
    static PlayerState original(){
        PlayerState s=new PlayerState();
        for(String key:Arrays.asList("a","b","c"))
            s.tracks.put(key,new PlayerState.Track(key,"content://media/"+key,key,"artist","album","Music",10000,100));
        s.createPlaylist("old","Old",false);s.add("old","a");s.select(false,"old","a",3000);
        s.addBookmark("a","My note",2000);
        return s;
    }
    static PhonePlaylistImport.Spec list(String id,String name,boolean book,String...ids){
        return new PhonePlaylistImport.Spec(id,name,book,Arrays.asList(ids));
    }
    public static void main(String[] args)throws Exception {
        PlayerState current=original();byte[] unchanged=StateCodec.encode(current);
        List<PhonePlaylistImport.Spec> stale=Arrays.asList(
          list("p1","Music",false,"c","missing1","a","missing2","b"),
          list("p2","Old audiobook",true,"missing3"),
          list("p3","Empty by choice",false));
        PhonePlaylistImport.Prepared pre=PhonePlaylistImport.prepare(current,stale);
        ok(pre.playlists.size()==3,"all playlist definitions retained");
        ok(pre.keptReferences==3,"known refs counted");
        ok(pre.missingReferences==3,"unknown refs counted");
        ok(pre.affectedPlaylists==2,"two affected playlists counted");
        ok(pre.emptiedPlaylists==1,"one playlist emptied by unknown refs");
        ok(pre.playlists.get(0).keys.equals(Arrays.asList("c","a","b")),"all surviving refs in original order");
        ok(pre.playlists.get(1).keys.isEmpty(),"unmatched playlist is retained empty");
        ok(pre.playlists.get(1).audiobook,"audiobook flag retained");
        ok(Arrays.equals(StateCodec.encode(current),unchanged),"preflight never mutates live state");
        PlayerState saved=StateMutation.prepareAndSave(current,
          next->PhonePlaylistImport.apply(next,pre.playlists),raw->true);
        ok(saved!=current,"commit persisted new candidate");
        ok(saved.playlists.size()==3 && !saved.playlists.containsKey("old"),"replacement semantics retained");
        ok(saved.getPlaylist("p1").entries.equals(Arrays.asList("c","a","b")),"committed order retained");
        ok(saved.getPlaylist("p2").entries.isEmpty(),"empty playlist valid");
        ok(saved.music.playlistId.isEmpty(),"invalid position reset");
        ok(saved.bookmarks.size()==1 && saved.bookmarks.get(0).trackKey.equals("a"),"bookmarks retained");
        ok(saved.tracks.size()==3,"tracks untouched");
        ok(Arrays.equals(StateCodec.encode(current),unchanged),"original state still exact");
        PlayerState fail=StateMutation.prepareAndSave(current,
          next->PhonePlaylistImport.apply(next,pre.playlists),raw->false);
        ok(fail==current,"failed persist does not publish replacement");
        reject(()->PhonePlaylistImport.prepare(current,Arrays.asList(list("p","bad",false,"a","a"))),"duplicates still invalid");
        reject(()->PhonePlaylistImport.prepare(current,Arrays.asList(list("x","dup",false,"a"),list("y","Dup",false,"c"))),"duplicate name still invalid");
        reject(()->PhonePlaylistImport.prepare(current,Arrays.asList(list("x","a",false,"a"),list("x","b",true,"b"))),"duplicate id still invalid");
        reject(()->PhonePlaylistImport.prepare(current,Arrays.asList(list("p","bad\nname",false,"a"))),"bad label still invalid");
        reject(()->PhonePlaylistImport.prepare(current,null),"null list still invalid");
        ok(PhonePlaylistImport.prepare(current,new ArrayList<>()).playlists.isEmpty(),"explicit empty playlist set permitted with warning in UI");
        System.out.println("StalePlaylistImport PASS "+assertions+" assertions (pure Java, no Android UI/phone)");
    }
}
