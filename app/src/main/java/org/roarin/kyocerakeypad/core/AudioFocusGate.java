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

    public void onExplicitRequest(boolean granted) {
        requestActive = granted;
        focusHeld = granted;
        interrupted = !granted;
    }
    public void onLoss() {
        focusHeld = false;
        interrupted = true;
    }
    public void onGain() {
        if(requestActive) focusHeld = true;
        // Do not clear interrupted: never resume automatically after a call.
    }
    public void onAbandon() {
        requestActive = false;
        focusHeld = false;
        interrupted = true;
    }
    public boolean canStart() {
        return requestActive && focusHeld && !interrupted;
    }
}
