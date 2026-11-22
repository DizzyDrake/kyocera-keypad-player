package org.roarin.kyocerakeypad.core;

/**
 * Deterministic focus state independent of Android. Only a successful *explicit*
 * Play request can clear the interruption latch. GAIN never autoplays.
 * Activity must additionally check its foreground PlaybackGate.
 */
public final class AudioFocusGate {
    private boolean requestActive;
    private boolean focusHeld;
    private boolean interrupted = true;
    // Only transient audio focus loss may be cleared by a later GAIN callback.
    // Permanent loss, calls and explicit Stop remain latched until explicit Play.
    private boolean transientInterrupted;

    public void onExplicitRequest(boolean granted) {
        requestActive = granted;
        focusHeld = granted;
        interrupted = !granted;
        transientInterrupted = false;
    }
    public void onLoss() {
        focusHeld = false;
        interrupted = true;
        transientInterrupted = false;
    }
    /** Short audio interruption: retain the original granted focus request. */
    public void onTransientLoss() {
        focusHeld = false;
        interrupted = true;
        transientInterrupted = requestActive;
    }
    public void onGain() {
        if(requestActive) {
            focusHeld = true;
            if(transientInterrupted) interrupted = false;
        }
        transientInterrupted = false;
        // Permanent LOSS, abandoned focus or unsolicited GAIN never clears latch.
    }
    public void onAbandon() {
        requestActive = false;
        focusHeld = false;
        interrupted = true;
        transientInterrupted = false;
    }
    public boolean canStart() {
        return requestActive && focusHeld && !interrupted;
    }
}
