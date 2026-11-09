import java.util.*;
import java.nio.charset.StandardCharsets;
import org.roarin.kyocerakeypad.core.*;

/** All filenames/IDs invented. Pure Java; no Android or filesystem mutation. */
public final class LibraryAvailabilityTests {
    private static int checks=0;
    private static void check(boolean value,String name){if(!value)throw new AssertionError(name);checks++;}
    private static PlayerState fake(){
        PlayerState s=new PlayerState();
        for(int i=1;i<=4;i++) {
            String key="media://"+i;
            s.tracks.put(key,new PlayerState.Track(key,key,"Track "+i,"Artist","Album","Music/",50000,500));
        }
        PlayerState.Playlist p=s.createPlaylist("p1","Favorites",false);
        p.entries.addAll(Arrays.asList("media://1","media://2","media://3","media://4"));
        s.createPlaylist("p2","Audiobook",true).entries.add("media://2");
        s.select(false,"p1","media://1",9000);
        s.select(true,"p2","media://2",10000);
        s.addBookmark("media://2","Lost Bookmark",1000);
        s.addBookmark("media://3","Keep Bookmark",2000);
        return s;
    }
    public static void main(String[] args)throws Exception {
        PlayerState s=fake();
        byte[] original=StateCodec.encode(s);
        Set<String> available=new HashSet<>(Arrays.asList("media://3","media://4"));
        LibraryAvailability.Preview view=LibraryAvailability.project(s,available);
        check(Arrays.equals(original,StateCodec.encode(s)),"preview leaves original untouched");
        check(view.unavailableTracks==2,"two stale tracks");
        check(view.removedPlaylistEntries==3,"three stale references across lists");
        check(view.affectedPlaylists==2,"two playlists affected");
        check(view.removedBookmarks==1,"only unavailable bookmark dropped");
        check(view.clearedProgress==2,"both unavailable positions reset");
        check(view.state.tracks.size()==2,"current two tracks retained");
        check(view.state.playlists.size()==2,"playlist shells preserved");
        check(view.state.getPlaylist("p1").entries.equals(Arrays.asList("media://3","media://4")),"order survives");
        check(view.state.getPlaylist("p2").entries.isEmpty(),"unavailable playlist becomes empty");
        check(view.state.bookmarks.size()==1 && "media://3".equals(view.state.bookmarks.get(0).trackKey),"available bookmark retained");
        check(view.state.music.playlistId.isEmpty() && view.state.book.playlistId.isEmpty(),"no orphan progress");
        Map<String,String> paths=new HashMap<>();paths.put("media://3","Music/New3.mp3");paths.put("media://4","Music/New4.mp3");
        byte[] exported=PhoneSnapshotExport.encode(view.state,paths);
        if(args.length>0)java.nio.file.Files.write(java.nio.file.Paths.get(args[0]),exported);
        String json=new String(exported,StandardCharsets.UTF_8);
        check(json.contains("kyocera-phone-snapshot-v0.1-PROVISIONAL"),"bridge schema retained");
        check(json.contains("Music/New3.mp3") && json.contains("Music/New4.mp3"),"available tracks present");
        check(!json.contains("media://1") && !json.contains("media://2"),"stale tracks omitted from export");
        check(json.indexOf("media://3")<json.indexOf("media://4"),"ordering retained in JSON");
        LibraryAvailability.pruneInPlace(s,available);
        check(Arrays.equals(StateCodec.encode(s),StateCodec.encode(view.state)),"explicit cleanup equals projection");
        check(Arrays.equals(StateCodec.encode(s),StateCodec.encode(LibraryAvailability.project(s,available).state)),"cleanup idempotent");
        PlayerState another=fake();
        Set<String> all=new HashSet<>(another.tracks.keySet());
        check(Arrays.equals(StateCodec.encode(another),StateCodec.encode(LibraryAvailability.project(another,all).state)),"all available unchanged");
        PlayerState zero=fake();
        LibraryAvailability.Preview none=LibraryAvailability.project(zero,Collections.emptySet());
        check(none.state.tracks.isEmpty(),"empty library still exportable");
        check(none.state.playlists.size()==2 && none.state.getPlaylist("p1").entries.isEmpty(),"playlist shells retained when empty");
        check(PhoneSnapshotExport.encode(none.state,Collections.emptyMap()).length>0,"empty but valid snapshot exported");
        check(Arrays.equals(original,StateCodec.encode(zero)),"empty projection leaves source unchanged");
        try{LibraryAvailability.project(null,available);throw new AssertionError("accepted null");}
        catch(IllegalArgumentException expected){checks++;}
        System.out.println("PASS "+checks+" missing-media projection/cleanup assertions (fictional pure Java)");
    }
}
