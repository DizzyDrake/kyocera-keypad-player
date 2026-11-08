import org.roarin.kyocerakeypad.core.SleepTimerPolicy;

public final class SleepTimerPolicyTests {
    private static int count;
    private static void check(boolean ok,String label){count++;if(!ok)throw new AssertionError(label);}
    private static void bad(String raw){
        boolean thrown=false;try{SleepTimerPolicy.durationMs(raw);}catch(IllegalArgumentException e){thrown=true;}
        check(thrown,"reject "+raw);
    }
    public static void main(String[] args){
        check(SleepTimerPolicy.durationMs("10")==600000L,"10 minutes");
        check(SleepTimerPolicy.durationMs("15")==900000L,"15 minutes");
        check(SleepTimerPolicy.durationMs("30")==1800000L,"30 minutes");
        check(SleepTimerPolicy.durationMs("60")==3600000L,"60 minutes");
        check(SleepTimerPolicy.durationMs(" 121 ")==7260000L,"custom > 60");
        check(SleepTimerPolicy.durationMs("2147483647")==128849018820000L,"large integer no 60m cap");
        bad(null);bad("");bad("0");bad("-5");bad("1.5");bad("10min");bad("99999999999999999999999");
        check(SleepTimerPolicy.remainingMs(1000L,1000L)==0,"expired");
        check(SleepTimerPolicy.remainingMs(1100L,1000L)==0,"overdue");
        check(SleepTimerPolicy.remainingMs(1000L,61000L)==60000L,"countdown");
        check(SleepTimerPolicy.rewindPosition(15000L,0)==15000L,"rewind Off");
        check(SleepTimerPolicy.rewindPosition(15000L,5)==10000L,"rewind 5s");
        check(SleepTimerPolicy.rewindPosition(15000L,10)==5000L,"rewind 10s");
        check(SleepTimerPolicy.rewindPosition(3000L,5)==0L,"clamp 3s");
        check(SleepTimerPolicy.rewindPosition(0L,10)==0L,"clamp zero");
        boolean badMode=false;try{SleepTimerPolicy.rewindPosition(15000L,7);}catch(IllegalArgumentException e){badMode=true;}
        check(badMode,"reject unapproved rewind");
        System.out.println("SleepTimerPolicyTests: "+count+" checks PASS");
    }
}
