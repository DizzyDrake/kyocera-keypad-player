package org.roarin.kyocerakeypad.core;

import java.io.*;
import java.util.*;

/** Versioned, length-bounded binary snapshot. App writes it with Android AtomicFile. */
public final class StateCodec {
    private StateCodec() {}
    private static final int MAGIC=0x4b595031, VERSION=1, MAX=100000;
    public static byte[] encode(PlayerState s) throws IOException {
        ByteArrayOutputStream out=new ByteArrayOutputStream();
        DataOutputStream d=new DataOutputStream(out);
        d.writeInt(MAGIC);d.writeInt(VERSION);
        d.writeInt(s.tracks.size());
        for(PlayerState.Track t:s.tracks.values()) {
            d.writeUTF(t.key);d.writeUTF(t.uri);d.writeUTF(t.title);d.writeUTF(t.artist);
            d.writeUTF(t.album);d.writeUTF(t.folder);d.writeLong(t.durationMs);d.writeLong(t.sizeBytes);
        }
        d.writeInt(s.playlists.size());
        for(PlayerState.Playlist p:s.playlists.values()) {
            d.writeUTF(p.id);d.writeUTF(p.name);d.writeBoolean(p.audiobook);
            d.writeInt(p.entries.size());for(String key:p.entries)d.writeUTF(key);
        }
        writeProgress(d,s.music);writeProgress(d,s.book);
        d.writeInt(s.bookmarks.size());
        for(PlayerState.Bookmark b:s.bookmarks) { d.writeUTF(b.trackKey);d.writeUTF(b.name);d.writeLong(b.positionMs); }
        d.flush();
        if(out.size()>16*1024*1024)throw new IOException("Snapshot exceeds 16 MiB");
        return out.toByteArray();
    }
    private static void writeProgress(DataOutputStream d,PlayerState.Progress p)throws IOException{
        d.writeUTF(p.playlistId);d.writeUTF(p.trackKey);d.writeLong(p.positionMs);
    }
    private static int count(DataInputStream d) throws IOException {
        int n=d.readInt();if(n<0 || n>MAX)throw new IOException("Invalid record count");return n;
    }
    public static PlayerState decode(byte[] bytes)throws IOException{
        if(bytes.length>16*1024*1024)throw new IOException("Snapshot exceeds 16 MiB");
        DataInputStream d=new DataInputStream(new ByteArrayInputStream(bytes));
        if(d.readInt()!=MAGIC || d.readInt()!=VERSION)throw new IOException("Unknown snapshot format");
        PlayerState s=new PlayerState();
        int n=count(d);
        for(int i=0;i<n;i++){
            PlayerState.Track t=new PlayerState.Track(d.readUTF(),d.readUTF(),d.readUTF(),d.readUTF(),
                    d.readUTF(),d.readUTF(),d.readLong(),d.readLong());
            if(s.tracks.put(t.key,t)!=null)throw new IOException("Duplicate track identity");
        }
        n=count(d);
        for(int i=0;i<n;i++){
            String id=d.readUTF(),name=d.readUTF();boolean book=d.readBoolean();
            if(s.playlists.containsKey(id))throw new IOException("Duplicate playlist identity");
            PlayerState.Playlist p=s.createPlaylist(id,name,book);
            int m=count(d);
            for(int j=0;j<m;j++)p.entries.add(d.readUTF());
        }
        readProgress(d,s.music);readProgress(d,s.book);
        n=count(d);
        for(int i=0;i<n;i++)s.bookmarks.add(new PlayerState.Bookmark(d.readUTF(),d.readUTF(),d.readLong()));
        if(d.available()!=0)throw new IOException("Unexpected trailing bytes");
        return s;
    }
    private static void readProgress(DataInputStream d,PlayerState.Progress p)throws IOException{
        p.playlistId=d.readUTF();p.trackKey=d.readUTF();p.positionMs=d.readLong();
        if(p.positionMs<0)throw new IOException("Negative playback position");
    }
}
