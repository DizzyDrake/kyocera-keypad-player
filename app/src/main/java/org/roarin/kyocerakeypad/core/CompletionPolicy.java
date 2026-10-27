package org.roarin.kyocerakeypad.core;

/**
 * Guard for MediaPlayer completion events. A callback queued before a call,
 * lifecycle pause or manual pause may arrive after playback authorization was
 * withdrawn. Never use such a callback to request fresh focus/auto-advance.
 * This is a pure-Java policy, not an Android timing guarantee.
 */
public final class CompletionPolicy {
    private CompletionPolicy() {}
    public static boolean mayAdvance(PlaybackGate playback, AudioFocusGate focus) {
        return playback.canStart() && focus.canStart();
    }
}
