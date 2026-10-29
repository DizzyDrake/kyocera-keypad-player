import org.roarin.kyocerakeypad.core.PlayerState;
import org.roarin.kyocerakeypad.core.StateCodec;
/** Fictional pure-Java state serialization; NOT an Android MediaPlayer test. */
public class FailedOpenSelectionTests {
  static int assertions=0;
  static void eq(Object a,Object b){assertions++;if(!a.equals(b))throw new AssertionError(a+" != "+b);}
  static PlayerState state() {
    PlayerState s=new PlayerState();
    s.tracks.put("musicA",new PlayerState.Track("musicA","content://fictional/1","Music A","","","",100000,12));
    s.tracks.put("musicB",new PlayerState.Track("musicB","content://fictional/2","Music B","","","",100000,12));
    s.tracks.put("bookA",new PlayerState.Track("bookA","content://fictional/3","Book A","","","",100000,12));
    s.tracks.put("bookB",new PlayerState.Track("bookB","content://fictional/4","Book B","","","",100000,12));
    PlayerState.Playlist music=s.createPlaylist("M","Music",false);
    music.entries.add("musicA");music.entries.add("musicB");
    PlayerState.Playlist book=s.createPlaylist("B","Book",true);
    book.entries.add("bookA");book.entries.add("bookB");
    s.select(false,"M","musicA",42000);
    s.select(true,"B","bookA",72000);
    return s;
  }
  public static void main(String[] args)throws Exception{
    PlayerState s=state();
    PlayerState.Progress previousMusic=new PlayerState.Progress(s.music);
    PlayerState.Progress previousBook=new PlayerState.Progress(s.book);
    s.select(false,"M","musicB",0);
    PlayerState persistedBeforeFailedOpen=StateCodec.decode(StateCodec.encode(s));
    eq(persistedBeforeFailedOpen.music.trackKey,"musicB");
    eq(persistedBeforeFailedOpen.music.positionMs,0L);
    eq(persistedBeforeFailedOpen.book.trackKey,"bookA");
    // A synchronous setDataSource exception or pre-prepare onError now occurs.
    // Existing frozen Activity stops player but does not restore selection.
    s.music.restoreFrom(previousMusic); // proposed correction's pure state effect
    PlayerState restored=StateCodec.decode(StateCodec.encode(s));
    eq(restored.music.trackKey,"musicA");eq(restored.music.positionMs,42000L);
    eq(restored.book.trackKey,"bookA");eq(restored.book.positionMs,72000L);
    s.select(true,"B","bookB",0);
    eq(StateCodec.decode(StateCodec.encode(s)).book.trackKey,"bookB");
    s.book.restoreFrom(previousBook);
    restored=StateCodec.decode(StateCodec.encode(s));
    eq(restored.book.trackKey,"bookA");eq(restored.book.positionMs,72000L);
    eq(restored.music.trackKey,"musicA");eq(restored.music.positionMs,42000L);
    System.out.println("PASS "+assertions+" fictional state/serialization assertions; Android playback not executed");
  }
}
