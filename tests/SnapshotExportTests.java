import java.io.*;
import java.nio.file.*;
import java.util.*;
import org.roarin.kyocerakeypad.core.*;

/** Invented only; no Android, audio or owner files. */
public final class SnapshotExportTests {
    private static int passed=0;
    private static void ok(boolean value,String name){if(!value)throw new AssertionError(name);passed++;}
    private static void rejects(Runnable r,String name){
        try{r.run();throw new AssertionError("Accepted "+name);}
        catch(IllegalArgumentException expected){passed++;}
    }
    private static PlayerState fake(){
        PlayerState s=new PlayerState();
        s.tracks.put("content://media/external/audio/media/10",new PlayerState.Track("content://media/external/audio/media/10","content://media/external/audio/media/10","Béta","Band","Fiction","Music/",60000,123));
        s.tracks.put("content://media/external/audio/media/20",new PlayerState.Track("content://media/external/audio/media/20","content://media/external/audio/media/20","Alpha","Band","Fiction","Music/",70000,321));
        s.tracks.put("content://media/external/audio/media/30",new PlayerState.Track("content://media/external/audio/media/30","content://media/external/audio/media/30","Chapter 1","Author","Fiction","Books/",100000,567));
        PlayerState.Playlist m=s.createPlaylist("music-1","Owner order",false);
        m.entries.add("content://media/external/audio/media/10");m.entries.add("content://media/external/audio/media/20");
        PlayerState.Playlist b=s.createPlaylist("book-1","Story",true);b.entries.add("content://media/external/audio/media/30");
        s.select(false,"music-1","content://media/external/audio/media/10",12500);
        s.select(true,"book-1","content://media/external/audio/media/30",45000);
        s.addBookmark("content://media/external/audio/media/30","Resume here",45000);
        return s;
    }
    private static Map<String,String> paths(PlayerState s){
        HashMap<String,String> m=new HashMap<>();int n=0;
        for(String key:s.tracks.keySet())m.put(key,++n==3?"Books/Chapter01.mp3":"Music/Track"+n+".mp3");
        return m;
    }
    public static void main(String[] args)throws Exception {
        PlayerState s=fake();Map<String,String> paths=paths(s);
        byte[] a=PhoneSnapshotExport.encode(s,paths),b=PhoneSnapshotExport.encode(s,paths);
        String json=new String(a,java.nio.charset.StandardCharsets.UTF_8);
        ok(Arrays.equals(a,b),"deterministic export");
        ok(json.contains("kyocera-phone-snapshot-v0.1-PROVISIONAL"),"bridge schema");
        ok(json.contains("appstate-"),"state digest identity");
        ok(json.contains("Béta"),"UTF-8 text");
        ok(json.indexOf("Track1.mp3")<json.indexOf("Track2.mp3"),"track ordering");
        ok(json.indexOf("music-1")<json.indexOf("book-1"),"playlist order");
        ok(json.contains("\"position_ms\":12500"),"music progress");
        ok(json.contains("\"position_ms\":45000"),"book progress and bookmark");
        ok(json.contains("Resume here"),"bookmark");
        ok(json.length()>100 && a.length<=PhoneSnapshotExport.MAX_BYTES,"bounded nonempty");
        ok(PhoneSnapshotExport.relativePath("Music/","x.mp3").equals("Music/x.mp3"),"relative path");
        rejects(()->PhoneSnapshotExport.relativePath("/Music/","x.mp3"),"absolute");
        rejects(()->PhoneSnapshotExport.relativePath("Music/../","x.mp3"),"traversal");
        rejects(()->PhoneSnapshotExport.relativePath("Music/","../x.mp3"),"slash in filename");
        rejects(()->PhoneSnapshotExport.relativePath("Music","x.mp3"),"missing folder slash");
        rejects(()->PhoneSnapshotExport.relativePath("C:/","x.mp3"),"drive path");
        Map<String,String> missing=new HashMap<>(paths);missing.remove(s.tracks.keySet().iterator().next());
        rejects(()->{try{PhoneSnapshotExport.encode(s,missing);}catch(IOException e){throw new AssertionError(e);}},"missing media path");
        Map<String,String> dup=new HashMap<>(paths);Iterator<String> keys=s.tracks.keySet().iterator();String k1=keys.next(),k2=keys.next();dup.put(k2,dup.get(k1).toUpperCase(Locale.ROOT));
        rejects(()->{try{PhoneSnapshotExport.encode(s,dup);}catch(IOException e){throw new AssertionError(e);}},"duplicate path");
        s.getPlaylist("music-1").entries.add("missing-key");
        rejects(()->{try{PhoneSnapshotExport.encode(s,paths);}catch(IOException e){throw new AssertionError(e);}},"orphan entry");
        s.getPlaylist("music-1").entries.remove("missing-key");
        s.getPlaylist("music-1").entries.add("content://media/external/audio/media/10");
        rejects(()->{try{PhoneSnapshotExport.encode(s,paths);}catch(IOException e){throw new AssertionError(e);}},"duplicate entry");
        s.getPlaylist("music-1").entries.remove(2);
        s.renamePlaylist("book-1","owner ORDER");
        rejects(()->{try{PhoneSnapshotExport.encode(s,paths);}catch(IOException e){throw new AssertionError(e);}},"duplicate playlist name");
        s.renamePlaylist("book-1","Story");
        s.music.trackKey="missing-key";
        rejects(()->{try{PhoneSnapshotExport.encode(s,paths);}catch(IOException e){throw new AssertionError(e);}},"orphan progress");
        s.music.trackKey="content://media/external/audio/media/10";
        byte[] changed=PhoneSnapshotExport.encode(s,paths);
        ok(Arrays.equals(a,changed),"restored state matches");
        s.move("music-1",0,1);
        ok(!Arrays.equals(a,PhoneSnapshotExport.encode(s,paths)),"state digest changes on reorder");
        if(args.length>0)Files.write(Paths.get(args[0]),a);
        System.out.println("PASS "+passed+" snapshot export assertions (pure Java; Android uncompiled)");
    }
}
