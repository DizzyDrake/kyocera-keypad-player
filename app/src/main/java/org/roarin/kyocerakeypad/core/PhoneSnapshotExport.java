package org.roarin.kyocerakeypad.core;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

/**
 * WQ147 WHAT: Build metadata-only, WQ146-compatible phone snapshot bytes.
 * WHY: PC editing needs explicit track identity, exact playlist order and progress.
 * IF CHANGED: rerun SnapshotExportTests and Python WQ146 validate_phone/phone_to_pc.
 * No Android APIs, audio reads, network, filesystem writes or imports here.
 */
public final class PhoneSnapshotExport {
    private PhoneSnapshotExport() {}
    public static final String SCHEMA = "kyocera-phone-snapshot-v0.1-PROVISIONAL";
    public static final int MAX_BYTES = 8_000_000;

    public static String relativePath(String relativeFolder, String displayName) {
        if (relativeFolder == null || displayName == null || displayName.isEmpty())
            throw new IllegalArgumentException("MediaStore relative folder/name missing");
        if ((!relativeFolder.isEmpty() && !relativeFolder.endsWith("/")) || displayName.contains("/") || displayName.contains("\\") || displayName.equals(".") || displayName.equals(".."))
            throw new IllegalArgumentException("Unsafe media filename");
        String path = relativeFolder + displayName;
        if (path.startsWith("/") || path.startsWith("\\") || path.contains("\\") || path.indexOf(':') >= 0)
            throw new IllegalArgumentException("Unsafe media path");
        for (String part : path.split("/", -1)) {
            if (part.isEmpty() || part.equals(".") || part.equals(".."))
                throw new IllegalArgumentException("Unsafe media path component");
        }
        return path;
    }
    private static String text(String value, String label, int max) {
        if (value == null || value.trim().isEmpty() || value.length() > max)
            throw new IllegalArgumentException("Invalid " + label);
        for (int i=0;i<value.length();i++) if (value.charAt(i)<32)
            throw new IllegalArgumentException("Control character in " + label);
        return value;
    }
    private static String optional(String value, String label, int max) {
        if (value == null) return "";
        if (value.length()>max) throw new IllegalArgumentException("Oversize "+label);
        for (int i=0;i<value.length();i++) if (value.charAt(i)<32)
            throw new IllegalArgumentException("Control character in "+label);
        return value;
    }
    private static void quote(StringBuilder b, String s) {
        b.append('"');
        for (int i=0;i<s.length();i++) {
            char c=s.charAt(i);
            switch(c) {
                case '"': b.append("\\\"");break;
                case '\\': b.append("\\\\");break;
                case '\b': b.append("\\b");break;
                case '\f': b.append("\\f");break;
                case '\n': b.append("\\n");break;
                case '\r': b.append("\\r");break;
                case '\t': b.append("\\t");break;
                default:
                    if(c<32) b.append(String.format(Locale.ROOT,"\\u%04x",(int)c));
                    else b.append(c);
            }
        }
        b.append('"');
    }
    private static void field(StringBuilder b, String name, String value) {
        quote(b,name);b.append(':');quote(b,value);
    }
    private static void number(StringBuilder b, String name, long value) {
        quote(b,name);b.append(':').append(value);
    }
    private static String digest(byte[] data) {
        try {
            byte[] raw=MessageDigest.getInstance("SHA-256").digest(data);
            StringBuilder b=new StringBuilder(raw.length*2);
            for(byte c:raw) b.append(String.format(Locale.ROOT,"%02x",c&255));
            return b.toString();
        } catch(NoSuchAlgorithmException e) {throw new IllegalStateException(e);}
    }
    private static void progress(StringBuilder b, PlayerState s, PlayerState.Progress p, boolean book) {
        if(!p.playlistId.isEmpty() || !p.trackKey.isEmpty()) {
            PlayerState.Playlist pl=s.playlists.get(p.playlistId);
            if(pl==null || pl.audiobook!=book || !pl.entries.contains(p.trackKey))
                throw new IllegalArgumentException("Saved playback context is inconsistent");
        }
        if(p.positionMs<0 || p.positionMs>1_000_000_000_000_000L)throw new IllegalArgumentException("Invalid playback position");
        b.append('{');field(b,"playlist_id",p.playlistId);b.append(',');field(b,"track_key",p.trackKey);
        b.append(',');number(b,"position_ms",p.positionMs);b.append('}');
    }
    public static byte[] encode(PlayerState s, Map<String,String> mediaPaths) throws IOException {
        if(s==null || mediaPaths==null)throw new IllegalArgumentException("Missing state/media paths");
        if(s.tracks.size()>50000 || s.playlists.size()>1000 || s.bookmarks.size()>10000)
            throw new IllegalArgumentException("Too many records for provisional bridge");
        StringBuilder b=new StringBuilder(4096);
        b.append('{');field(b,"schema",SCHEMA);b.append(',');
        field(b,"snapshot_id","appstate-"+digest(StateCodec.encode(s)));
        b.append(',');number(b,"revision",0);b.append(',');
        b.append("\"tracks\":[");
        HashSet<String> paths=new HashSet<>();int index=0;
        for(PlayerState.Track t:s.tracks.values()) {
            if(index++>0)b.append(',');
            String key=text(t.key,"track key",200);
            String path=text(mediaPaths.get(key),"track relative path",2000);
            if(!paths.add(path.toLowerCase(Locale.ROOT)))
                throw new IllegalArgumentException("Ambiguous case-insensitive relative path");
            int lastSlash=path.lastIndexOf('/');
            relativePath(lastSlash<0?"":path.substring(0,lastSlash+1),path.substring(lastSlash+1)); // validate complete path
            b.append('{');field(b,"key",key);b.append(',');field(b,"path",path);
            b.append(',');field(b,"title",optional(t.title,"title",2000));
            b.append(',');field(b,"artist",optional(t.artist,"artist",2000));
            b.append(',');field(b,"album",optional(t.album,"album",2000));
            if(t.durationMs>10_000_000_000L || t.sizeBytes>1_000_000_000_000_000L)
                throw new IllegalArgumentException("Track metadata exceeds bridge bounds");
            b.append(',');number(b,"duration_ms",t.durationMs);
            b.append(',');number(b,"size_bytes",t.sizeBytes);b.append('}');
        }
        b.append("],\"playlists\":[");index=0;
        HashSet<String> names=new HashSet<>();
        for(PlayerState.Playlist p:s.playlists.values()) {
            if(index++>0)b.append(',');
            text(p.id,"playlist ID",200);text(p.name,"playlist name",200);
            if(!names.add(p.name.toLowerCase(Locale.ROOT)))
                throw new IllegalArgumentException("Duplicate playlist name");
            if(p.entries.size()>50000)throw new IllegalArgumentException("Too many playlist entries");
            b.append('{');field(b,"id",p.id);b.append(',');field(b,"name",p.name);
            b.append(",\"audiobook\":").append(p.audiobook?"true":"false");
            b.append(",\"track_keys\":[");
            HashSet<String> seen=new HashSet<>();int j=0;
            for(String key:p.entries){
                if(!s.tracks.containsKey(key) || !seen.add(key))
                    throw new IllegalArgumentException("Unknown/duplicate playlist track");
                if(j++>0)b.append(',');quote(b,key);
            }
            b.append("]}");
        }
        b.append("],\"music\":");progress(b,s,s.music,false);
        b.append(",\"book\":");progress(b,s,s.book,true);
        b.append(",\"bookmarks\":[");index=0;
        for(PlayerState.Bookmark m:s.bookmarks) {
            if(!s.tracks.containsKey(m.trackKey) || m.positionMs>1_000_000_000_000_000L)throw new IllegalArgumentException("Invalid bookmark");
            if(index++>0)b.append(',');
            b.append('{');field(b,"track_key",m.trackKey);b.append(',');
            field(b,"name",text(m.name,"bookmark name",1000));b.append(',');
            number(b,"position_ms",m.positionMs);b.append('}');
        }
        b.append("]}\n");
        byte[] data=b.toString().getBytes(StandardCharsets.UTF_8);
        if(data.length>MAX_BYTES)throw new IOException("Snapshot exceeds 8 MB bridge limit");
        return data;
    }
}
