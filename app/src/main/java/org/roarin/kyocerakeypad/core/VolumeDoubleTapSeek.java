package org.roarin.kyocerakeypad.core;

/**
 * Source-only/opt-in experiment for the specific Kyocera + headset trial.
 * Interprets observed system MUSIC volume-index *changes*, not raw Bluetooth
 * key presses; any rapid local volume adjustments can also trigger a seek.
 * One sample may coalesce multiple inputs; ambiguous changes are ignored.
 * Offline clock is elapsedRealtime() in caller; no wall-clock dependency.
 */
public final class VolumeDoubleTapSeek {
    public enum Action { NONE, FORWARD_30S, BACK_15S }
    private static final int UNSET=Integer.MIN_VALUE;
    private static final long COOLDOWN_MS=850L;
    private final long maxGapMs;
    private int lastVolume=UNSET;
    private int firstDirection=0;
    private long firstAt=-1L;
    private long cooldownUntil=-1L;

    public VolumeDoubleTapSeek(long maxGapMs) {
        if(maxGapMs<=0L)throw new IllegalArgumentException("maxGapMs");
        this.maxGapMs=maxGapMs;
    }
    /** Rebase when starting, stopping, pausing or reading the volume fails. */
    public void reset(int volume) {
        lastVolume=volume;
        firstDirection=0;
        firstAt=-1L;
        cooldownUntil=-1L;
    }
    public void clear() { reset(UNSET); }

    public Action observe(int volume,long elapsedMs) {
        if(lastVolume==UNSET){reset(volume);return Action.NONE;}
        int step=volume-lastVolume;
        lastVolume=volume;
        if(step==0)return Action.NONE;
        // A sampled jump of two or more indices might be an OS adjustment,
        // button hold, or two fast presses; do not assert which caused it.
        if(step!=1 && step!=-1){firstDirection=0;firstAt=-1;return Action.NONE;}
        if(elapsedMs<cooldownUntil){firstDirection=0;firstAt=-1;return Action.NONE;}
        if(firstDirection==step && firstAt>=0L && elapsedMs>=firstAt
                && elapsedMs-firstAt<=maxGapMs) {
            firstDirection=0;
            firstAt=-1L;
            cooldownUntil=elapsedMs+COOLDOWN_MS;
            // Owner trial correction: double DOWN advances 30s; double UP rewinds 15s.
            return step>0?Action.BACK_15S:Action.FORWARD_30S;
        }
        firstDirection=step;
        firstAt=elapsedMs;
        return Action.NONE;
    }
}
