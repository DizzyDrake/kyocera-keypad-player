import org.roarin.kyocerakeypad.core.AlphabetJump;
import java.util.*;

public class AlphabetJumpTests {
    private static int checked=0;
    private static void eq(Object actual,Object expected,String name) {
        checked++;
        if(!Objects.equals(actual,expected)) throw new AssertionError(name+": expected "+expected+" got "+actual);
    }
    public static void main(String[] args) {
        eq(AlphabetJump.bucket("Apple"),'A',"ordinary");
        eq(AlphabetJump.bucket(" apple "),'A',"trim");
        eq(AlphabetJump.bucket("Écho"),'E',"accent");
        eq(AlphabetJump.bucket("über"),'U',"umlaut");
        eq(AlphabetJump.bucket("42 intro"),'#',"digit");
        eq(AlphabetJump.bucket("'quoted"),'#',"punctuation");
        eq(AlphabetJump.bucket("你好"),'#',"non-Latin");
        eq(AlphabetJump.bucket(""),'#',"empty");
        eq(AlphabetJump.bucket(null),'#',"null");
        eq(AlphabetJump.bucket(" \t"),'#',"whitespace");
        eq(AlphabetJump.bucket("ßeta"),'S',"uppercase expansion");
        List<String> all=Arrays.asList("42 intro","Apple","Apricot","Écho","Epilogue","Zebra");
        eq(AlphabetJump.firstMatchingIndex(all,'A'),1,"A first index");
        eq(AlphabetJump.firstMatchingIndex(all,'E'),3,"E first index");
        eq(AlphabetJump.firstMatchingIndex(all,'Z'),5,"Z first index");
        eq(AlphabetJump.firstMatchingIndex(all,'#'),0,"number first index");
        eq(AlphabetJump.firstMatchingIndex(all,'Q'),-1,"absent");
        Map<Character,Integer> counts=AlphabetJump.counts(all);
        eq(counts.size(),4,"bucket count");
        eq(new ArrayList<>(counts.keySet()),Arrays.asList('A','E','Z','#'),"order");
        eq(counts.get('A'),2,"A count");
        eq(counts.get('E'),2,"E count");
        eq(counts.get('Z'),1,"Z count");
        eq(counts.get('#'),1,"hash count");
        eq(AlphabetJump.counts(Collections.emptyList()).isEmpty(),true,"no titles");
        eq(AlphabetJump.firstMatchingIndex(Collections.emptyList(),'A'),-1,"empty lookup");
        List<String> filtered=Arrays.asList("Écho","Zebra");
        eq(AlphabetJump.counts(filtered).containsKey('A'),false,"filter respects visible subset");
        eq(AlphabetJump.firstMatchingIndex(filtered,'E'),0,"filtered first index");
        System.out.println("PASS "+checked+" AlphabetJump assertions");
    }
}
