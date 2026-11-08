import org.roarin.kyocerakeypad.core.VolumeDoubleTapSeek;
import static org.roarin.kyocerakeypad.core.VolumeDoubleTapSeek.Action.*;
public final class VolumeDoubleTapSeekTests {
    private static int cases;
    private static void expect(String description, VolumeDoubleTapSeek.Action actual, VolumeDoubleTapSeek.Action expected) {
        cases++;
        if (actual != expected) throw new AssertionError(description+" expected "+expected+" got "+actual);
    }
    private static VolumeDoubleTapSeek fresh(int at) {
        VolumeDoubleTapSeek d=new VolumeDoubleTapSeek(650);
        d.reset(at);
        return d;
    }
    public static void main(String[] args) {
        VolumeDoubleTapSeek d=fresh(5);
        // Actual owner probe structure: +1 followed by +1 at 202ms distance.
        expect("first up",d.observe(6,10830),NONE);
        expect("second up rewinds",d.observe(7,11032),BACK_15S);
        expect("no repeat unchanged",d.observe(7,11135),NONE);
        expect("cooldown up ignored",d.observe(8,11235),NONE);
        expect("cooldown down ignored",d.observe(7,11435),NONE);
        // Clear/rebase on pause or restart.
        d.reset(8);
        expect("first down",d.observe(7,24132),NONE);
        expect("second down advances",d.observe(6,24336),FORWARD_30S);
        // Another actual owner report pattern: 8->7, then 7->6 203ms later.
        d.reset(8);
        expect("report third down first",d.observe(7,34662),NONE);
        expect("report third down second",d.observe(6,34865),FORWARD_30S);
        d.reset(6);
        expect("slow first",d.observe(7,2000),NONE);
        expect("slow second outside window",d.observe(8,2651),NONE);
        d.reset(6);
        expect("direction first",d.observe(7,1000),NONE);
        expect("direction reversal",d.observe(6,1100),NONE);
        expect("direction reversal repeated",d.observe(5,1200),FORWARD_30S);
        d.reset(8);
        expect("combined two-index change deliberately ignored",d.observe(10,1000),NONE);
        expect("new first after combined",d.observe(11,1100),NONE);
        expect("new second after combined",d.observe(12,1220),BACK_15S);
        d.reset(15);
        expect("at max no index change",d.observe(15,1000),NONE);
        expect("at max no index change twice",d.observe(15,1200),NONE);
        d.reset(8);
        expect("first before pause",d.observe(9,1000),NONE);
        d.reset(9); // pause or disabled setting
        expect("after pause does not inherit prior press",d.observe(10,1100),NONE);
        d.clear();
        expect("after clear baseline",d.observe(10,1400),NONE);
        expect("after clear first actual change",d.observe(11,1500),NONE);
        expect("after clear second actual change",d.observe(12,1600),BACK_15S);
        System.out.println("PASS "+cases+" volume detector assertions");
    }
}
