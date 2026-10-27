import org.roarin.kyocerakeypad.core.*;
import java.io.*;
import java.util.*;
public final class StateTests {
  static int passed=0;
  static void yes(boolean b,String label){if(!b)throw new AssertionError(label);passed++;}
  static void fail(Runnable r,String label){boolean threw=false;try{r.run();}catch(IllegalArgumentException e){threw=true;}yes(threw,label);}
  static PlayerState fresh(){
    PlayerState s=new PlayerState();
    s.tracks.put("media:17",new PlayerState.Track("media:17","content://media/external/audio/media/17","Zèbre","a","b","folder",120000,101));
    s.tracks.put("media:18",new PlayerState.Track("media:18","content://media/external/audio/media/18","Aardvark","a","b","folder",30000,102));
    s.tracks.put("media:19",new PlayerState.Track("media:19","content://media/external/audio/media/19","Ginkgo","a","b","folder",300000,103));
    return s;
  }
  public static void main(String[] args)throws Exception{
    PlayerState s=fresh();
    s.createPlaylist("p1","Music",false);s.createPlaylist("p2","Book",true);
    s.add("p1","media:17");s.add("p1","media:18");s.add("p1","media:19");
    yes(s.getPlaylist("p1").entries.equals(Arrays.asList("media:17","media:18","media:19")),"insertion order");
    s.move("p1",2,0);
    yes(s.getPlaylist("p1").entries.equals(Arrays.asList("media:19","media:17","media:18")),"manual nonalphabetic order");
    s.select(false,"p1","media:17",42420);
    s.add("p2","media:19");s.select(true,"p2","media:19",18420);
    yes(s.music.positionMs==42420 && s.book.positionMs==18420,"two contexts");
    s.savePosition(false,121000);yes(s.music.positionMs==120000,"clamp to duration");
    yes(s.seek("media:18",0,-10000)==0,"back 10 at start");
    yes(s.seek("media:18",29999,10000)==30000,"forward 10 at end");
    yes(s.seek("media:18",25000,-10000)==15000,"back 10 within track");
    yes(s.seek("media:18",25000,10000)==30000,"forward 10 within track");
    yes(s.seek("media:18",Long.MAX_VALUE,10000)==30000,"seek overflow clamp");
    s.addBookmark("media:19","Chapter 1",18420);
    s.addBookmark("media:19","Later",21000);
    yes(s.bookmarksFor("media:19").size()==2,"multiple bookmarks");
    s.addBookmark("media:18","Clamped",999999);
    yes(s.bookmarksFor("media:18").get(0).positionMs==30000,"bookmark clamped");
    s.renameBookmark(0,"Start");yes(s.bookmarksFor("media:19").get(0).name.equals("Start"),"rename bookmark");
    s.deleteBookmark(1);yes(s.bookmarksFor("media:19").size()==1,"delete bookmark");
    byte[] data=StateCodec.encode(s);PlayerState round=StateCodec.decode(data);
    yes(round.getPlaylist("p1").entries.equals(s.getPlaylist("p1").entries),"order persisted");
    yes(round.music.positionMs==120000 && round.book.positionMs==18420,"both contexts persisted");
    yes(round.bookmarksFor("media:19").get(0).name.equals("Start"),"bookmarks persisted");
    yes(round.tracks.get("media:17").title.equals("Zèbre"),"Unicode persisted");
    yes(Arrays.equals(data,StateCodec.encode(round)),"deterministic serialization");
    round.renamePlaylist("p1","Renamed");yes(round.getPlaylist("p1").name.equals("Renamed"),"rename playlist");
    round.remove("p1",1);yes(round.getPlaylist("p1").entries.size()==2,"remove entry");
    fail(()->round.select(true,"p1","media:17",0),"cross-context reject");
    fail(()->round.add("p1","unknown"),"unknown track reject");
    fail(()->round.add("p1","media:19"),"duplicate track reject");
    fail(()->round.move("p1",3,0),"invalid index reject");
    fail(()->round.clamp("missing",123),"missing identity no title remap");
    byte[] broken=data.clone();broken[0]=0;boolean rejected=false;
    try{StateCodec.decode(broken);}catch(IOException e){rejected=true;}
    yes(rejected,"corrupt magic reject");
    byte[] appended=Arrays.copyOf(data,data.length+1);rejected=false;
    try{StateCodec.decode(appended);}catch(IOException e){rejected=true;}
    yes(rejected,"trailing bytes reject");
    byte[] truncated=Arrays.copyOf(data,data.length-3);rejected=false;
    try{StateCodec.decode(truncated);}catch(IOException e){rejected=true;}
    yes(rejected,"truncated snapshot reject");
    fail(()->round.createPlaylist("p2","Duplicate",true),"duplicate playlist identity reject");
    round.deletePlaylist("p1");yes(round.music.playlistId.isEmpty(),"deleted playlist clears music context");
    yes(round.book.playlistId.equals("p2"),"delete music preserves audiobook");
    System.out.println("PASS "+passed+" assertions (pure Java core; Android UI not compiled)");
  }
}
