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

    /** A stable, current-state selection. Never combine a new index with an
     *  old Playlist object captured before a copy-persist-publish mutation.
     *  Null means stop at the end, after a removal, or after context changed.
     *  This method is Android-free and does not request audio focus.
     */
    public static final class NextSelection {
        public final PlayerState.Playlist playlist;
        public final int index;
        private NextSelection(PlayerState.Playlist playlist,int index) {
            this.playlist=playlist; this.index=index;
        }
    }
    public static NextSelection nextSelection(PlayerState state,String playlistId,
                                               String completedKey,boolean audiobook) {
        if(state==null || playlistId==null || completedKey==null)return null;
        PlayerState.Progress current=state.progress(audiobook);
        if(!playlistId.equals(current.playlistId) || !completedKey.equals(current.trackKey))return null;
        PlayerState.Playlist playlist=state.playlists.get(playlistId);
        if(playlist==null || playlist.audiobook!=audiobook)return null;
        int currentIndex=playlist.entries.indexOf(completedKey);
        if(currentIndex<0 || currentIndex+1>=playlist.entries.size())return null;
        int nextIndex=currentIndex+1;
        if(!state.tracks.containsKey(playlist.entries.get(nextIndex)))return null;
        return new NextSelection(playlist,nextIndex);
    }

}
