package org.roarin.kyocerakeypad.core;

import java.io.IOException;

/**
 * A late pre-prepare MediaPlayer failure must not resurrect progress that a
 * newer, successfully committed playlist edit has removed. Work against the
 * CURRENT state, never the old state object captured when playback began.
 *
 * The caller must first verify that the callback belongs to its MediaPlayer
 * and that preparation never succeeded. This class contains no Android APIs.
 */
public final class FailedOpenRollback {
    private FailedOpenRollback() {}

    public enum Outcome {
        RESTORED,
        SKIPPED_SELECTION_CHANGED,
        SKIPPED_INVALID_PREVIOUS,
        SAVE_FAILED
    }

    public static final class Result {
        public final PlayerState state;
        public final Outcome outcome;
        private Result(PlayerState state, Outcome outcome) {
            this.state = state;
            this.outcome = outcome;
        }
        public boolean restored() { return outcome == Outcome.RESTORED; }
    }

    /**
     * Rebase the old listening selection onto the latest durable state ONLY
     * when the failed pending selection still occupies the relevant progress
     * slot, and the old selection remains a valid playlist/track identity.
     * Other committed edits (e.g. bookmarks) survive this copy-persist-publish
     * operation. If a playlist was deleted or the selected track changed,
     * refuse rollback rather than writing an orphaned context.
     *
     * A writer failure leaves the original state object untouched. The caller
     * must publish Result.state only when outcome == RESTORED.
     */
    public static Result attempt(PlayerState current, boolean book,
            String pendingPlaylist, String pendingTrack,
            PlayerState.Progress previous, StateMutation.Writer writer) throws IOException {
        if (current == null || pendingPlaylist == null || pendingTrack == null ||
                previous == null || writer == null) {
            throw new IllegalArgumentException("Missing rollback argument");
        }
        PlayerState.Progress now = current.progress(book);
        if (!pendingPlaylist.equals(now.playlistId) || !pendingTrack.equals(now.trackKey)) {
            return new Result(current, Outcome.SKIPPED_SELECTION_CHANGED);
        }
        if (!validPrevious(current, book, previous)) {
            return new Result(current, Outcome.SKIPPED_INVALID_PREVIOUS);
        }
        // Copy the latest committed state and save BEFORE publishing it.
        PlayerState next = StateMutation.prepareAndSave(current,
                candidate -> candidate.progress(book).restoreFrom(previous), writer);
        if (next == current) return new Result(current, Outcome.SAVE_FAILED);
        return new Result(next, Outcome.RESTORED);
    }

    private static boolean validPrevious(PlayerState state, boolean book, PlayerState.Progress p) {
        if (p.playlistId.isEmpty() || p.trackKey.isEmpty()) {
            return p.playlistId.isEmpty() && p.trackKey.isEmpty() && p.positionMs == 0;
        }
        PlayerState.Playlist playlist = state.playlists.get(p.playlistId);
        PlayerState.Track track = state.tracks.get(p.trackKey);
        return playlist != null && playlist.audiobook == book &&
                playlist.entries.contains(p.trackKey) && track != null &&
                p.positionMs >= 0 && p.positionMs <= track.durationMs;
    }
}
