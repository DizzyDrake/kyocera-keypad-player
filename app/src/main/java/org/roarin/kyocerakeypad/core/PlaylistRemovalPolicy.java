package org.roarin.kyocerakeypad.core;

import java.util.ArrayList;
import java.util.List;

/**
 * Chooses the next eligible entry before an active playlist track is removed.
 * Never opens a file, mutates an audio file, or edits the saved playlist.
 */
public final class PlaylistRemovalPolicy {
    private PlaylistRemovalPolicy() {}

    /**
     * The remaining order follows the active shuffled session when its exact
     * membership is valid, otherwise the saved playlist order. A final-track
     * removal stops at the end unless explicit playlist repeat is active.
     */
    public static String successor(List<String> saved, List<String> activeOrder,
            String current, boolean repeatPlaylist) {
        if (saved == null || current == null || !saved.contains(current))
            throw new IllegalArgumentException("Current entry is not in playlist");
        List<String> basis = saved;
        if (activeOrder != null && activeOrder.size() == saved.size() &&
                activeOrder.containsAll(saved) && saved.containsAll(activeOrder))
            basis = activeOrder;
        int at = basis.indexOf(current);
        for (int i=at+1;i<basis.size();i++)
            if (!current.equals(basis.get(i))) return basis.get(i);
        if (repeatPlaylist)
            for (int i=0;i<at;i++)
                if (!current.equals(basis.get(i))) return basis.get(i);
        return null;
    }

    /** A paused/inactive saved session may choose the next listed item. */
    public static String savedSuccessor(List<String> saved,String current) {
        return successor(saved,null,current,true);
    }
}
