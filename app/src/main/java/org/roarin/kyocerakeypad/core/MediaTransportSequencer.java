package org.roarin.kyocerakeypad.core;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Pure-Java, UI-independent interpretation of *already normalized* headset media
 * key DOWN events. Not a MediaSession, playback service, or device key capture.
 *
 * All methods must be called on the same serialized callback thread. The caller
 * must schedule flush() at the deadline when double-seek mode is enabled.
 * Double-seek is deliberately disabled by default until E4831/headset event
 * traces establish whether double NEXT/PREVIOUS is distinguishable.
 */
public final class MediaTransportSequencer {
    public enum Key { NEXT, PREVIOUS, PLAY, PAUSE, PLAY_PAUSE, STOP, UNKNOWN }
    public enum Action { NEXT, PREVIOUS, PLAY, PAUSE, TOGGLE, STOP, SEEK_FORWARD_10S, SEEK_BACK_10S }

    private final long doublePressWindowMs;
    private boolean doubleSeekEnabled;
    private Key pending = null;
    private long pendingAtMs;

    public MediaTransportSequencer(long doublePressWindowMs) {
        if (doublePressWindowMs < 100 || doublePressWindowMs > 1000)
            throw new IllegalArgumentException("Double-press window must be 100..1000 ms");
        this.doublePressWindowMs = doublePressWindowMs;
    }

    public boolean isDoubleSeekEnabled() { return doubleSeekEnabled; }

    /** Changing mapping drains any pending single action rather than dropping it. */
    public List<Action> setDoubleSeekEnabled(boolean enabled) {
        List<Action> out = drainPending();
        doubleSeekEnabled = enabled;
        return out;
    }

    /**
     * Process a single normalized non-repeated ACTION_DOWN. Ignore ACTION_UP,
     * key repeats and duplicate deliveries in the Android adapter, not here.
     * nowMs should be SystemClock.elapsedRealtime() from that adapter.
     */
    public List<Action> onPress(Key key, long nowMs) {
        if (key == null) key = Key.UNKNOWN;
        List<Action> out = new ArrayList<>();
        if (pending != null && (nowMs < pendingAtMs || nowMs - pendingAtMs >= doublePressWindowMs))
            out.addAll(drainPending());
        if (key == Key.UNKNOWN) return out;
        if (key == Key.NEXT || key == Key.PREVIOUS) {
            if (!doubleSeekEnabled) {
                out.add(key == Key.NEXT ? Action.NEXT : Action.PREVIOUS);
            } else if (pending == key && nowMs >= pendingAtMs) {
                pending = null;
                out.add(key == Key.NEXT ? Action.SEEK_FORWARD_10S : Action.SEEK_BACK_10S);
            } else {
                out.addAll(drainPending());
                pending = key;
                pendingAtMs = nowMs;
            }
            return out;
        }
        out.addAll(drainPending());
        switch (key) {
            case PLAY: out.add(Action.PLAY); break;
            case PAUSE: out.add(Action.PAUSE); break;
            case PLAY_PAUSE: out.add(Action.TOGGLE); break;
            case STOP: out.add(Action.STOP); break;
            default: break;
        }
        return out;
    }

    /** Must be scheduled by Android service at pendingAt + doublePressWindowMs. */
    public List<Action> flush(long nowMs) {
        if (pending != null && (nowMs < pendingAtMs || nowMs - pendingAtMs >= doublePressWindowMs))
            return drainPending();
        return Collections.emptyList();
    }

    /** Flush before service stop, session replacement or mapping changes. */
    public List<Action> close() { return drainPending(); }

    public boolean hasPending() { return pending != null; }
    public long pendingDeadlineMs() { return pending == null ? -1 : pendingAtMs + doublePressWindowMs; }

    private List<Action> drainPending() {
        if (pending == null) return Collections.emptyList();
        Action action = pending == Key.NEXT ? Action.NEXT : Action.PREVIOUS;
        pending = null;
        return Collections.singletonList(action);
    }
}
