package org.roarin.kyocerakeypad.core;

import java.util.*;

/**
 * A read-only view of currently available audio IDs, plus an explicit cleanup
 * operation for a StateMutation candidate. Never matches tracks by title/path,
 * never deletes audio, and never alters the source while preparing an export.
 */
public final class LibraryAvailability {
    private LibraryAvailability() {}

    public static final class Preview {
        public final PlayerState state;
        public final int unavailableTracks, removedPlaylistEntries, affectedPlaylists;
        public final int removedBookmarks, clearedProgress;
        private Preview(PlayerState state, int unavailableTracks, int removedPlaylistEntries,
                int affectedPlaylists, int removedBookmarks, int clearedProgress) {
            this.state=state;
            this.unavailableTracks=unavailableTracks;
            this.removedPlaylistEntries=removedPlaylistEntries;
            this.affectedPlaylists=affectedPlaylists;
            this.removedBookmarks=removedBookmarks;
            this.clearedProgress=clearedProgress;
        }
    }

    /** Build a detached state containing only observed safe media IDs. */
    public static Preview project(PlayerState original, Set<String> availableKeys) {
        if(original==null || availableKeys==null)throw new IllegalArgumentException("Missing source/library IDs");
        PlayerState current=new PlayerState();
        for(Map.Entry<String,PlayerState.Track> e:original.tracks.entrySet())
            if(availableKeys.contains(e.getKey()))current.tracks.put(e.getKey(),e.getValue());
        int dropped=0,affected=0;
        for(PlayerState.Playlist old:original.playlists.values()) {
            PlayerState.Playlist next=current.createPlaylist(old.id,old.name,old.audiobook);
            for(String key:old.entries) {
                if(current.tracks.containsKey(key))next.entries.add(key);
                else dropped++;
            }
            if(next.entries.size()!=old.entries.size())affected++;
        }
        int cleared=0;
        if(copyValidProgress(original.music,current.music,current,false))cleared++;
        if(copyValidProgress(original.book,current.book,current,true))cleared++;
        for(PlayerState.Bookmark mark:original.bookmarks)
            if(current.tracks.containsKey(mark.trackKey))current.bookmarks.add(mark);
        return new Preview(current, original.tracks.size()-current.tracks.size(),dropped,affected,
                original.bookmarks.size()-current.bookmarks.size(),cleared);
    }
    /** Returns true if an old (non-empty) playback context was cleared. */
    private static boolean copyValidProgress(PlayerState.Progress from,PlayerState.Progress to,
            PlayerState target,boolean audiobook) {
        if(from.playlistId.isEmpty() && from.trackKey.isEmpty())return false;
        PlayerState.Playlist playlist=target.playlists.get(from.playlistId);
        if(playlist!=null && playlist.audiobook==audiobook &&
                target.tracks.containsKey(from.trackKey) && playlist.entries.contains(from.trackKey)) {
            to.restoreFrom(from);
            return false;
        }
        return true;
    }
    /**
     * Only call inside StateMutation.prepareAndSave, after owner confirmation.
     * Construct the complete safe replacement before touching the candidate.
     */
    public static void pruneInPlace(PlayerState candidate,Set<String> availableKeys) {
        Preview view=project(candidate,availableKeys);
        candidate.tracks.clear();candidate.tracks.putAll(view.state.tracks);
        candidate.playlists.clear();candidate.playlists.putAll(view.state.playlists);
        candidate.bookmarks.clear();candidate.bookmarks.addAll(view.state.bookmarks);
        candidate.music.restoreFrom(view.state.music);
        candidate.book.restoreFrom(view.state.book);
    }
}
