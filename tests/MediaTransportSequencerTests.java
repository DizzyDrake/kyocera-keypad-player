import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import org.roarin.kyocerakeypad.core.MediaTransportSequencer;
import org.roarin.kyocerakeypad.core.MediaTransportSequencer.Action;
import org.roarin.kyocerakeypad.core.MediaTransportSequencer.Key;

public final class MediaTransportSequencerTests {
    private static int count;
    private static void check(String label, List<Action> got, Action... expected) {
        List<Action> want = Arrays.asList(expected);
        if (!got.equals(want)) throw new AssertionError(label + " expected " + want + " got " + got);
        count++;
    }
    private static void truth(String label, boolean value) {
        if (!value) throw new AssertionError(label);
        count++;
    }
    public static void main(String[] args) {
        MediaTransportSequencer s = new MediaTransportSequencer(350);
        truth("default double-seek off", !s.isDoubleSeekEnabled());
        check("single next immediate",s.onPress(Key.NEXT,100),Action.NEXT);
        check("single previous immediate",s.onPress(Key.PREVIOUS,110),Action.PREVIOUS);
        check("play/pause immediate",s.onPress(Key.PLAY_PAUSE,120),Action.TOGGLE);
        check("unknown ignored",s.onPress(Key.UNKNOWN,125));
        check("enable double mode",s.setDoubleSeekEnabled(true));
        check("first next held",s.onPress(Key.NEXT,1000));
        truth("deadline",s.pendingDeadlineMs()==1350);
        check("premature flush",s.flush(1349));
        check("double next seek",s.onPress(Key.NEXT,1349),Action.SEEK_FORWARD_10S);
        truth("double clears",!s.hasPending());
        check("first previous held",s.onPress(Key.PREVIOUS,2000));
        check("double previous seek",s.onPress(Key.PREVIOUS,2200),Action.SEEK_BACK_10S);
        check("next held",s.onPress(Key.NEXT,3000));
        check("single next at deadline",s.flush(3350),Action.NEXT);
        check("flush idempotent",s.flush(3351));
        check("previous held",s.onPress(Key.PREVIOUS,4000));
        check("mixed direction emits prior",s.onPress(Key.NEXT,4100),Action.PREVIOUS);
        check("then next pending",s.flush(4450),Action.NEXT);
        check("pending next",s.onPress(Key.NEXT,5000));
        check("pause flushes prior first",s.onPress(Key.PAUSE,5100),Action.NEXT,Action.PAUSE);
        check("play",s.onPress(Key.PLAY,5200),Action.PLAY);
        check("stop",s.onPress(Key.STOP,5300),Action.STOP);
        check("pending previous",s.onPress(Key.PREVIOUS,6000));
        check("clock regression drains pending",s.onPress(Key.NEXT,5000),Action.PREVIOUS);
        check("close flushes pending",s.close(),Action.NEXT);
        check("close idempotent",s.close());
        check("pending next before disabling",s.onPress(Key.NEXT,7000));
        check("disable drains pending",s.setDoubleSeekEnabled(false),Action.NEXT);
        check("immediate again",s.onPress(Key.NEXT,7100),Action.NEXT);
        boolean threw=false;
        try { new MediaTransportSequencer(99); } catch(IllegalArgumentException expected){threw=true;}
        truth("invalid window rejected",threw);
        System.out.println("PASS " + count + " MediaTransportSequencer checks");
    }
}
