package org.roarin.kyocerakeypad.core;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

/** Session-only playback order. Never mutates PlayerState.Playlist.entries. */
public final class PlaylistPlaybackOrder {
    public enum Repeat { OFF, PLAYLIST, TRACK }
    private final ArrayList<String> order = new ArrayList<>();
    private String playlistId = "";

    /** Start with the explicitly selected item. For shuffle, shuffle the rest. */
    public void start(String id, List<String> savedEntries, String first,
                      boolean shuffle, Random random) {
        if (id == null || savedEntries == null || !savedEntries.contains(first))
            throw new IllegalArgumentException("Selected track not in playlist");
        ArrayList<String> fresh = new ArrayList<>(savedEntries);
        if (shuffle) {
            fresh.remove(first);
            Collections.shuffle(fresh, random);
            fresh.add(0, first);
        }
        order.clear(); order.addAll(fresh); playlistId = id;
    }
    public boolean matches(String id, List<String> savedEntries, String current) {
        if (!playlistId.equals(id) || !order.contains(current) || order.size()!=savedEntries.size())return false;
        return order.containsAll(savedEntries) && savedEntries.containsAll(order);
    }
    public String next(String current, int direction, Repeat repeat, boolean automatic) {
        if (automatic && repeat==Repeat.TRACK && order.contains(current))return current;
        int at=order.indexOf(current);
        if (at<0 || (direction!=1 && direction!=-1))return null;
        int next=at+direction;
        if (next>=0 && next<order.size())return order.get(next);
        if (repeat==Repeat.PLAYLIST && !order.isEmpty())return order.get(next<0?order.size()-1:0);
        return null;
    }
    public List<String> snapshot() { return new ArrayList<>(order); }
}
