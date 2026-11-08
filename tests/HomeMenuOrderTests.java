import java.util.*;
import org.roarin.kyocerakeypad.core.HomeMenuOrder;
public class HomeMenuOrderTests {
  static int n=0;
  static void check(boolean ok,String msg){n++;if(!ok)throw new AssertionError(msg);}
  public static void main(String[] args){
    HomeMenuOrder d=HomeMenuOrder.defaults();
    check(d.size()==9,"nine actions");
    check(d.get(0).equals("resume_music"),"music first");
    check(d.get(1).equals("resume_audiobook"),"book second");
    check(d.snapshot().size()==9,"snapshot count");
    check(d.indexOf("help")==7,"help default");
    check(!d.move("help",7),"same index no-op");
    check(d.move("help",0),"help moved to first");
    check(d.get(0).equals("help"),"first digit dynamic");
    check(d.indexOf("resume_music")==1,"music shifted");
    check(d.move("help",8),"help to bottom");
    check(d.get(8).equals("help"),"last digit dynamic");
    HomeMenuOrder saved=HomeMenuOrder.parse(d.serialize());
    check(saved.snapshot().equals(d.snapshot()),"roundtrip");
    check(saved.move("about",0),"edit copy");
    check(!saved.snapshot().equals(d.snapshot()),"copy isolation");
    check(!d.move("absent",0),"reject unknown");
    check(!d.move("help",9),"reject out of range");
    check(!d.move("help",-1),"reject negative");
    check(HomeMenuOrder.parse(null).snapshot().equals(HomeMenuOrder.DEFAULT),"null default");
    check(HomeMenuOrder.parse("").snapshot().equals(HomeMenuOrder.DEFAULT),"empty default");
    check(HomeMenuOrder.parse("help").snapshot().equals(HomeMenuOrder.DEFAULT),"short default");
    check(HomeMenuOrder.parse("resume_music,resume_music,resume_music,resume_music,resume_music,resume_music,resume_music,resume_music,resume_music").snapshot().equals(HomeMenuOrder.DEFAULT),"duplicates default");
    check(HomeMenuOrder.parse(d.serialize().replace("help","unexpected")).snapshot().equals(HomeMenuOrder.DEFAULT),"unknown default");
    check(HomeMenuOrder.parse(d.serialize()+",").snapshot().equals(HomeMenuOrder.DEFAULT),"trailing comma default");
    try{d.snapshot().add("extra");throw new AssertionError("mutable snapshot");}catch(UnsupportedOperationException ok){n++;}
    check(d.size()==9,"original unaffected");
    System.out.println(n+"/"+n+" HomeMenuOrder model tests PASS");
  }
}
