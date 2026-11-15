package org.roarin.kyocerakeypad.core;

/**
 * Independent remote media Next/Previous mapping per listening lane.
 * This models media-button intent, not volume-level changes. Keypad-local
 * playlist navigation deliberately uses its separate track-skip route.
 * SPDX-License-Identifier: Apache-2.0
 */
public final class RemoteSkipPolicy {
    private RemoteSkipPolicy() {}
    public enum Action { NEXT_TRACK, PREVIOUS_TRACK, SEEK_FORWARD_30S, SEEK_BACK_15S }
    public static Action decide(boolean audiobook,boolean musicSeeks,boolean audiobookSeeks,boolean next){
        boolean seeks=audiobook?audiobookSeeks:musicSeeks;
        if(seeks)return next?Action.SEEK_FORWARD_30S:Action.SEEK_BACK_15S;
        return next?Action.NEXT_TRACK:Action.PREVIOUS_TRACK;
    }
}
