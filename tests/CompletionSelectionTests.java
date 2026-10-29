import org.roarin.kyocerakeypad.core.*;

/** Executes real PlayerState and CompletionPolicy with fictional tracks. */
public final class CompletionSelectionTests {
    static int n=0;
    static void check(boolean yes,String why){n++;if(!yes)throw new AssertionError(why);}
    static PlayerState state(){
        PlayerState s=new PlayerState();
        for(String key:new String[]{"A","B","C","D","BOOK"})
            s.tracks.put(key,new PlayerState.Track(key,"content://fiction/"+key,key,"","","",100000,1));
        PlayerState.Playlist p=s.createPlaylist("music","Fictional",false);
        for(String key:new String[]{"A","B","C","D"})s.add(p.id,key);
        PlayerState.Playlist b=s.createPlaylist("book","Fictional Book",true);
        s.add(b.id,"BOOK");
        s.select(false,"music","A",500);
        s.select(true,"book","BOOK",2000);
        return s;
    }
    static void next(PlayerState s,String playlist,String current,boolean book,String expected){
        CompletionPolicy.NextSelection sel=CompletionPolicy.nextSelection(s,playlist,current,book);
        check(sel!=null,"expected selection "+expected);
        check(sel.playlist==s.playlists.get(playlist),"must reference current playlist instance");
        check(expected.equals(sel.playlist.entries.get(sel.index)),"wrong next track: "+expected);
    }
    static void none(PlayerState s,String playlist,String current,boolean book){
        check(CompletionPolicy.nextSelection(s,playlist,current,book)==null,"must stop rather than advance stale context");
    }
    public static void main(String[] args) throws Exception{
        PlayerState s=state();
        next(s,"music","A",false,"B");
        // The real copy-persist-publish state changes playlist identity.
        PlayerState before=s;
        PlayerState changed=StateCodec.decode(StateCodec.encode(s));
        changed.move("music",2,1); // A,C,B,D
        check(before.playlists.get("music")!=changed.playlists.get("music"),"fixture must replace object");
        next(changed,"music","A",false,"C");
        check("B".equals(before.playlists.get("music").entries.get(changed.nextIndex("music","A"))),
              "baseline stale playlist must reproduce wrong B");
        changed=StateCodec.decode(StateCodec.encode(s));
        changed.remove("music",1); // A,C,D
        next(changed,"music","A",false,"C");
        changed=StateCodec.decode(StateCodec.encode(s));
        changed.remove("music",0); // B,C,D, current A removed
        none(changed,"music","A",false);
        changed=StateCodec.decode(StateCodec.encode(s));
        changed.deletePlaylist("music");
        none(changed,"music","A",false);
        changed=StateCodec.decode(StateCodec.encode(s));
        changed.select(false,"music","B",100);
        none(changed,"music","A",false);
        none(s,"book","BOOK",false);
        none(s,"music","A",true);
        none(s,"book","BOOK",true); // end of audiobook playlist
        next(s,"music","A",false,"B"); // music independent of book
        s.tracks.remove("B");
        none(s,"music","A",false); // never substitute missing track
        System.out.println("PASS "+n+" completion-context assertions (real Java core, fictional tracks)");
    }
}
