package org.roarin.kyocerakeypad.core;

import java.util.*;

/** Deterministic offline state; no Android APIs and no filesystem access. */
public final class PlayerState {
    public static final class Track {
        public final String key, uri, title, artist, album, folder;
        public final long durationMs, sizeBytes;
        public Track(String key, String uri, String title, String artist, String album, String folder,
                     long durationMs, long sizeBytes) {
            this.key = required(key); this.uri = required(uri);
            this.title = safe(title); this.artist = safe(artist); this.album = safe(album); this.folder = safe(folder);
            this.durationMs = Math.max(0L, durationMs); this.sizeBytes = Math.max(0L, sizeBytes);
        }
    }
    public static final class Playlist {
        public final String id;
        public String name;
        public final boolean audiobook;
        public final ArrayList<String> entries = new ArrayList<>();
        public Playlist(String id, String name, boolean audiobook) {
            this.id = required(id); this.name = required(name); this.audiobook = audiobook;
        }
    }
    public static final class Progress {
        public String playlistId = "", trackKey = "";
        public long positionMs = 0L;
    }
    public static final class Bookmark {
        public final String trackKey, name;
        public final long positionMs;
        public Bookmark(String trackKey, String name, long positionMs) {
            this.trackKey = required(trackKey); this.name = required(name);
            this.positionMs = Math.max(0L, positionMs);
        }
    }
    public final LinkedHashMap<String, Track> tracks = new LinkedHashMap<>();
    public final LinkedHashMap<String, Playlist> playlists = new LinkedHashMap<>();
    public final Progress music = new Progress(), book = new Progress();
    public final ArrayList<Bookmark> bookmarks = new ArrayList<>();

    private static String safe(String s) { return s == null ? "" : s; }
    private static String required(String s) {
        if (s == null || s.trim().isEmpty()) throw new IllegalArgumentException("Required text missing");
        return s;
    }
    public Playlist createPlaylist(String id, String name, boolean audiobook) {
        if (playlists.containsKey(id)) throw new IllegalArgumentException("Duplicate playlist ID");
        Playlist p = new Playlist(id, name, audiobook);
        playlists.put(id, p); return p;
    }
    public void renamePlaylist(String id, String name) { getPlaylist(id).name = required(name); }
    public void deletePlaylist(String id) {
        if (playlists.remove(id) == null) throw new IllegalArgumentException("Playlist not found");
        if (music.playlistId.equals(id)) clear(music);
        if (book.playlistId.equals(id)) clear(book);
    }
    private static void clear(Progress p) { p.playlistId=""; p.trackKey=""; p.positionMs=0; }
    public Playlist getPlaylist(String id) {
        Playlist p=playlists.get(id);
        if(p==null) throw new IllegalArgumentException("Playlist not found: "+id);
        return p;
    }
    public void add(String playlistId, String trackKey) {
        if (!tracks.containsKey(trackKey)) throw new IllegalArgumentException("Track not in library");
        PlayerState.Playlist p=getPlaylist(playlistId);
        if(p.entries.contains(trackKey)) throw new IllegalArgumentException("Track already in playlist");
        p.entries.add(trackKey);
    }
    public void remove(String playlistId, int index) {
        Playlist p=getPlaylist(playlistId); check(index,p.entries.size()); p.entries.remove(index);
    }
    public void move(String playlistId, int from, int to) {
        Playlist p=getPlaylist(playlistId); check(from,p.entries.size()); check(to,p.entries.size());
        if(from!=to) p.entries.add(to,p.entries.remove(from));
    }
    private static void check(int i,int size) {
        if(i<0 || i>=size) throw new IllegalArgumentException("Entry index out of bounds");
    }
    public Progress progress(boolean audiobook) { return audiobook ? book : music; }
    public void select(boolean audiobook,String playlistId,String trackKey,long positionMs) {
        Playlist p=getPlaylist(playlistId);
        if(p.audiobook!=audiobook || !p.entries.contains(trackKey))
            throw new IllegalArgumentException("Track not in chosen playback context");
        Progress v=progress(audiobook);
        v.playlistId=playlistId;v.trackKey=trackKey;v.positionMs=clamp(trackKey,positionMs);
    }
    public void savePosition(boolean audiobook,long positionMs) {
        Progress p=progress(audiobook);
        if(!p.trackKey.isEmpty()) p.positionMs=clamp(p.trackKey,positionMs);
    }
    public long clamp(String trackKey,long positionMs) {
        Track t=tracks.get(trackKey);
        if(t==null) throw new IllegalArgumentException("Missing track identity; never substitute by title");
        return Math.min(t.durationMs,Math.max(0L,positionMs));
    }
    public long seek(String trackKey,long positionMs,long deltaMs) {
        long d=tracks.containsKey(trackKey)?tracks.get(trackKey).durationMs:0;
        if(!tracks.containsKey(trackKey)) throw new IllegalArgumentException("Missing track identity");
        if(deltaMs>0 && positionMs>Long.MAX_VALUE-deltaMs) return d;
        if(deltaMs<0 && positionMs<Long.MIN_VALUE-deltaMs) return 0;
        return clamp(trackKey,positionMs+deltaMs);
    }
    public void addBookmark(String trackKey,String name,long positionMs) {
        bookmarks.add(new Bookmark(trackKey,name,clamp(trackKey,positionMs)));
    }
    public void renameBookmark(int index,String newName) {
        Bookmark b=bookmarks.get(index);
        bookmarks.set(index,new Bookmark(b.trackKey,newName,b.positionMs));
    }
    public void deleteBookmark(int index) { bookmarks.remove(index); }
    public ArrayList<Bookmark> bookmarksFor(String trackKey) {
        ArrayList<Bookmark> found=new ArrayList<>();
        for(Bookmark b:bookmarks) if(b.trackKey.equals(trackKey)) found.add(b);
        return found;
    }
    public int nextIndex(String playlistId,String trackKey) {
        Playlist p=getPlaylist(playlistId);
        int i=p.entries.indexOf(trackKey);
        return i>=0 && i+1<p.entries.size() ? i+1 : -1;
    }
}
