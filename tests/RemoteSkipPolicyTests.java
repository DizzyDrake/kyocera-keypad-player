import org.roarin.kyocerakeypad.core.RemoteSkipPolicy;
import org.roarin.kyocerakeypad.core.RemoteSkipPolicy.Action;
/** Source-only host checks; no Android device/MediaSession dispatch implied. */
public final class RemoteSkipPolicyTests {
  private static int count;
  private static void check(boolean book,boolean music,boolean books,boolean next,Action expected){
    Action actual=RemoteSkipPolicy.decide(book,music,books,next);
    if(actual!=expected)throw new AssertionError("book="+book+" music="+music+" books="+books+" next="+next+": "+actual);
    count++;
  }
  public static void main(String[] args){
    for(boolean music:new boolean[]{false,true})for(boolean books:new boolean[]{false,true}){
      check(true,music,books,true,books?Action.SEEK_FORWARD_30S:Action.NEXT_TRACK);
      check(true,music,books,false,books?Action.SEEK_BACK_15S:Action.PREVIOUS_TRACK);
      check(false,music,books,true,music?Action.SEEK_FORWARD_30S:Action.NEXT_TRACK);
      check(false,music,books,false,music?Action.SEEK_BACK_15S:Action.PREVIOUS_TRACK);
    }
    System.out.println("PASS "+count+" RemoteSkipPolicy combinations");
  }
}
