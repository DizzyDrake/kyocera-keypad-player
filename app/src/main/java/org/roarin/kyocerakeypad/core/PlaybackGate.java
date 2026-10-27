package org.roarin.kyocerakeypad.core;

/**
 * Tiny lifecycle guard: playback is always an explicit foreground request.
 * Does not control MediaPlayer itself; the Android Activity must check canStart()
 * in every asynchronous prepared/seek-complete callback.
 */
public final class PlaybackGate {
    private boolean foreground;
    private boolean requested;

    public void onResume() { foreground = true; }
    public void onPause() { foreground = false; requested = false; }
    public void requestPlay() { requested = foreground; }
    public void requestPause() { requested = false; }
    public boolean canStart() { return foreground && requested; }
}
