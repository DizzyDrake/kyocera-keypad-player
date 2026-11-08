package org.roarin.kyocerakeypad.core;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;

/**
 * Offline playlist-only replacement. No Android API, disk writes, or media deletion.
 * The caller obtains confirmation after a pure preflight. Snapshot mismatches are
 * informational: stale import is owner-authorized, but unknown track IDs are omitted.
 * Pass a decoded-copy candidate to apply(), then write through StateMutation.
 */
public final class PhonePlaylistImport {
    private PhonePlaylistImport() {}
    public static final String SCHEMA = "kyocera-playlist-import-v0.1";
    public static final String FILENAME = "pc_playlist_import_v1.json";
    public static final int MAX_BYTES = 8_000_000;
    public static final class Spec {
        public final String id, name;
        public final boolean audiobook;
        public final ArrayList<String> keys;
        public Spec(String id, String name, boolean audiobook, List<String> keys) {
            this.id=id;this.name=name;this.audiobook=audiobook;
            this.keys=keys==null?null:new ArrayList<>(keys);
        }
    }
    private static void label(String s, String what) {
        if(s==null || s.trim().isEmpty() || s.length()>200)
            throw new IllegalArgumentException("Invalid "+what);
        for(int i=0;i<s.length();i++) if(s.charAt(i)<32)
            throw new IllegalArgumentException("Invalid "+what);
    }
    /**
     * Pure preflight for owner-approved stale imports. Preserve input playlist order and
     * every still-known track key in its original relative order. Unknown track keys
     * cannot be safely rebound to a different song and are skipped with counts.
     * Invalid structure and duplicate identities still fail before mutation.
     */
    public static final class Prepared {
        public final ArrayList<Spec> playlists;
        public final int missingReferences, affectedPlaylists, emptiedPlaylists, keptReferences;
        private Prepared(ArrayList<Spec> playlists, int missingReferences,
                         int affectedPlaylists, int emptiedPlaylists, int keptReferences) {
            this.playlists=playlists;
            this.missingReferences=missingReferences;
            this.affectedPlaylists=affectedPlaylists;
            this.emptiedPlaylists=emptiedPlaylists;
            this.keptReferences=keptReferences;
        }
    }
    public static Prepared prepare(PlayerState target, List<Spec> specs) {
        if(target==null || specs==null || specs.size()>1000)
            throw new IllegalArgumentException("Invalid playlist import list");
        HashSet<String> ids=new HashSet<>(), names=new HashSet<>();
        ArrayList<Spec> prepared=new ArrayList<>();
        int missing=0, affected=0, emptied=0, kept=0;
        for(Spec spec:specs) {
            if(spec==null)throw new IllegalArgumentException("Null playlist");
            label(spec.id,"playlist ID"); label(spec.name,"playlist name");
            if(!ids.add(spec.id) || !names.add(spec.name.toLowerCase(Locale.ROOT)))
                throw new IllegalArgumentException("Duplicate playlist ID/name");
            if(spec.keys==null || spec.keys.size()>50000)
                throw new IllegalArgumentException("Invalid playlist entries");
            HashSet<String> seen=new HashSet<>();
            ArrayList<String> available=new ArrayList<>();
            int beforeMissing=missing;
            for(String key:spec.keys) {
                if(key==null || key.trim().isEmpty() || !seen.add(key))
                    throw new IllegalArgumentException("Invalid/duplicate track identity");
                if(target.tracks.containsKey(key)) { available.add(key); kept++; }
                else missing++;
            }
            if(missing!=beforeMissing) affected++;
            if(!spec.keys.isEmpty() && available.isEmpty()) emptied++;
            prepared.add(new Spec(spec.id,spec.name,spec.audiobook,available));
        }
        return new Prepared(prepared,missing,affected,emptied,kept);
    }
    public static void apply(PlayerState target, List<Spec> specs) {
        if(target==null || specs==null || specs.size()>1000)
            throw new IllegalArgumentException("Invalid playlist import list");
        HashSet<String> ids=new HashSet<>(),names=new HashSet<>();
        // Fully validate before changing the candidate. Caller must still use a decoded copy.
        for(Spec spec:specs) {
            if(spec==null)throw new IllegalArgumentException("Null playlist");
            label(spec.id,"playlist ID");label(spec.name,"playlist name");
            if(!ids.add(spec.id) || !names.add(spec.name.toLowerCase(Locale.ROOT)))
                throw new IllegalArgumentException("Duplicate playlist ID/name");
            if(spec.keys==null || spec.keys.size()>50000)
                throw new IllegalArgumentException("Invalid playlist entries");
            HashSet<String> keys=new HashSet<>();
            for(String key:spec.keys){
                if(key==null || !target.tracks.containsKey(key) || !keys.add(key))
                    throw new IllegalArgumentException("Missing/duplicate track identity");
            }
        }
        target.playlists.clear();
        for(Spec spec:specs){
            PlayerState.Playlist p=target.createPlaylist(spec.id,spec.name,spec.audiobook);
            p.entries.addAll(spec.keys);
        }
        // Preserve a valid listening position; clear only contexts invalidated by
        // the playlist changes. Aurora accepts initial import resets if necessary.
        clearIfInvalid(target,target.music,false);
        clearIfInvalid(target,target.book,true);
        // Bookmarks deliberately preserved; track library and audio files unchanged.
    }
    private static void clearIfInvalid(PlayerState s, PlayerState.Progress p, boolean book) {
        if(p.playlistId.isEmpty() && p.trackKey.isEmpty())return;
        PlayerState.Playlist list=s.playlists.get(p.playlistId);
        if(list!=null && list.audiobook==book && list.entries.contains(p.trackKey))return;
        p.playlistId="";p.trackKey="";p.positionMs=0;
    }
}
