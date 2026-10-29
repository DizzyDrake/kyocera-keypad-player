import org.roarin.kyocerakeypad.core.*;
import java.io.IOException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

/** Pure Java fictional state/callback-order tests, NOT Android MediaPlayer tests. */
public class FailedOpenRollbackTests {
  static int n=0;
  static void ok(boolean b,String msg){n++;if(!b)throw new AssertionError(msg);}
  static void eq(Object a,Object b){ok(a.equals(b),a+" != "+b);}
  static PlayerState make(){
    PlayerState s=new PlayerState();
    for(String k:new String[]{"A","B","C","X"})s.tracks.put(k,
        new PlayerState.Track(k,"content://fictional/"+k,k,"","","",100000,1));
    PlayerState.Playlist p=s.createPlaylist("P","Music",false);
    p.entries.add("A");p.entries.add("B");p.entries.add("C");
    PlayerState.Playlist b=s.createPlaylist("Q","Books",true);b.entries.add("X");
    s.select(false,"P","A",72000);s.select(true,"Q","X",13000);
    return s;
  }
  static PlayerState.Progress prior(PlayerState s){return new PlayerState.Progress(s.music);}
  static void pending(PlayerState s){s.select(false,"P","B",0);}
  static FailedOpenRollback.Result rollback(PlayerState s,PlayerState.Progress p,StateMutation.Writer w)throws Exception{
    return FailedOpenRollback.attempt(s,false,"P","B",p,w);
  }
  static void normal()throws Exception{
    PlayerState s=make();PlayerState.Progress before=prior(s);pending(s);
    AtomicReference<byte[]> saved=new AtomicReference<>();
    FailedOpenRollback.Result r=rollback(s,before,bytes->{saved.set(bytes);return true;});
    eq(r.outcome,FailedOpenRollback.Outcome.RESTORED);
    ok(r.state!=s,"must publish a distinct copy");eq(s.music.trackKey,"B");
    eq(r.state.music.trackKey,"A");eq(r.state.music.positionMs,72000L);
    eq(r.state.book.trackKey,"X");eq(r.state.book.positionMs,13000L);
    eq(StateCodec.decode(saved.get()).music.trackKey,"A");
    // Repeated late callback after successful restore cannot reapply.
    eq(rollback(r.state,before,bytes->{throw new AssertionError("must not write");}).outcome,
        FailedOpenRollback.Outcome.SKIPPED_SELECTION_CHANGED);
  }
  static void deletedPlaylist()throws Exception{
    PlayerState s=make();PlayerState.Progress before=prior(s);pending(s);
    s=StateMutation.prepareAndSave(s,x->x.deletePlaylist("P"),bytes->true);
    PlayerState committed=s;AtomicInteger writes=new AtomicInteger();
    FailedOpenRollback.Result r=rollback(s,before,bytes->{writes.incrementAndGet();return true;});
    eq(r.outcome,FailedOpenRollback.Outcome.SKIPPED_SELECTION_CHANGED);
    ok(r.state==committed,"preserve committed deletion");eq(writes.get(),0);
    eq(r.state.music.playlistId,"");ok(!r.state.playlists.containsKey("P"),"deletion intact");
  }
  static void changedTrack()throws Exception{
    PlayerState s=make();PlayerState.Progress before=prior(s);pending(s);
    s=StateMutation.prepareAndSave(s,x->x.select(false,"P","C",5000),bytes->true);
    FailedOpenRollback.Result r=rollback(s,before,bytes->{throw new AssertionError("unexpected write");});
    eq(r.outcome,FailedOpenRollback.Outcome.SKIPPED_SELECTION_CHANGED);
    eq(r.state.music.trackKey,"C");eq(r.state.music.positionMs,5000L);
  }
  static void removedPrevious()throws Exception{
    PlayerState s=make();PlayerState.Progress before=prior(s);pending(s);
    s=StateMutation.prepareAndSave(s,x->x.remove("P",0),bytes->true);
    FailedOpenRollback.Result r=rollback(s,before,bytes->{throw new AssertionError("unexpected write");});
    eq(r.outcome,FailedOpenRollback.Outcome.SKIPPED_INVALID_PREVIOUS);
    eq(r.state.music.trackKey,"B");ok(!r.state.playlists.get("P").entries.contains("A"),"removal intact");
  }
  static void rebaseUnrelatedEdit()throws Exception{
    PlayerState s=make();PlayerState.Progress before=prior(s);pending(s);
    s=StateMutation.prepareAndSave(s,x->x.addBookmark("X","fictional note",3000),bytes->true);
    AtomicReference<byte[]> durable=new AtomicReference<>();
    FailedOpenRollback.Result r=rollback(s,before,bytes->{durable.set(bytes);return true;});
    eq(r.outcome,FailedOpenRollback.Outcome.RESTORED);
    eq(r.state.music.trackKey,"A");eq(r.state.book.trackKey,"X");
    eq(r.state.bookmarks.size(),1);eq(r.state.bookmarks.get(0).name,"fictional note");
    eq(StateCodec.decode(durable.get()).bookmarks.size(),1);
  }
  static void writeFailure()throws Exception{
    PlayerState s=make();PlayerState.Progress before=prior(s);pending(s);
    FailedOpenRollback.Result r=rollback(s,before,bytes->false);
    eq(r.outcome,FailedOpenRollback.Outcome.SAVE_FAILED);
    ok(r.state==s,"failed write must not publish copy");eq(s.music.trackKey,"B");
    boolean threw=false;
    try{rollback(s,before,bytes->{throw new IOException("fictional write failure");});}
    catch(IOException e){threw=true;}
    ok(threw,"propagate writer exception");eq(s.music.trackKey,"B");
  }
  static void invalidPrior()throws Exception{
    PlayerState s=make();pending(s);
    PlayerState.Progress old=new PlayerState.Progress();old.playlistId="DELETED";old.trackKey="A";
    FailedOpenRollback.Result r=rollback(s,old,bytes->{throw new AssertionError("unexpected write");});
    eq(r.outcome,FailedOpenRollback.Outcome.SKIPPED_INVALID_PREVIOUS);
    old=new PlayerState.Progress();old.playlistId="P";old.trackKey="A";old.positionMs=100001;
    eq(rollback(s,old,bytes->true).outcome,FailedOpenRollback.Outcome.SKIPPED_INVALID_PREVIOUS);
  }
  static void emptyPrior()throws Exception{
    PlayerState s=make();s.music.restoreFrom(new PlayerState.Progress());
    PlayerState.Progress before=prior(s);pending(s);
    FailedOpenRollback.Result r=rollback(s,before,bytes->true);
    eq(r.outcome,FailedOpenRollback.Outcome.RESTORED);
    eq(r.state.music.playlistId,"");eq(r.state.music.trackKey,"");eq(r.state.music.positionMs,0L);
  }
  static void bookIndependence()throws Exception{
    PlayerState s=make();PlayerState.Progress before=new PlayerState.Progress(s.book);
    s.select(true,"Q","X",0);
    FailedOpenRollback.Result r=FailedOpenRollback.attempt(s,true,"Q","X",before,bytes->true);
    eq(r.outcome,FailedOpenRollback.Outcome.RESTORED);
    eq(r.state.book.positionMs,13000L);eq(r.state.music.trackKey,"A");
  }
  public static void main(String[] args)throws Exception{
    normal();deletedPlaylist();changedTrack();removedPrevious();rebaseUnrelatedEdit();
    writeFailure();invalidPrior();emptyPrior();bookIndependence();
    System.out.println("PASS "+n+" actual-core fictional rollback assertions; Android not executed");
  }
}
