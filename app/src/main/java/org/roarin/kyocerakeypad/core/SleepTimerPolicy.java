package org.roarin.kyocerakeypad.core;

/** Pure time arithmetic for one-shot playback timer and optional audiobook resume rewind. */
public final class SleepTimerPolicy {
    private SleepTimerPolicy() {}
    public static long durationMs(String raw) {
        if (raw == null || !raw.trim().matches("[0-9]+"))
            throw new IllegalArgumentException("Enter a positive whole number of minutes");
        final long minutes;
        try { minutes = Long.parseLong(raw.trim()); }
        catch (NumberFormatException e) { throw new IllegalArgumentException("Minutes are too large"); }
        if (minutes <= 0 || minutes > Long.MAX_VALUE / 60000L)
            throw new IllegalArgumentException("Minutes must be positive and fit a timer");
        return minutes * 60000L;
    }
    public static long remainingMs(long nowElapsed, long deadlineElapsed) {
        return Math.max(0L, deadlineElapsed - nowElapsed);
    }
    public static long rewindPosition(long savedPositionMs, int rewindSeconds) {
        if (rewindSeconds != 0 && rewindSeconds != 5 && rewindSeconds != 10)
            throw new IllegalArgumentException("Audiobook rewind must be Off, 5 or 10 seconds");
        return Math.max(0L, Math.max(0L,savedPositionMs) - rewindSeconds * 1000L);
    }
}
