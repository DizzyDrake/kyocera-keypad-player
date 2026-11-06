package org.roarin.kyocerakeypad.core;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;

/** Stable home-menu identities, independent of display labels and Android widgets. */
public final class HomeMenuOrder {
    public static final List<String> DEFAULT=Collections.unmodifiableList(Arrays.asList(
        "resume_music", "resume_audiobook", "music_playlists", "audiobook_playlists",
        "browse_audio", "listening_settings", "export_metadata", "help", "about"));
    private final ArrayList<String> ids;
    private HomeMenuOrder(List<String> ids){this.ids=new ArrayList<>(ids);}
    public static HomeMenuOrder defaults(){return new HomeMenuOrder(DEFAULT);}
    /** Invalid/stale saved order falls back without modifying the saved preference. */
    public static HomeMenuOrder parse(String saved){
        if(saved==null || saved.isEmpty())return defaults();
        String[] parts=saved.split(",",-1);
        List<String> values=Arrays.asList(parts);
        if(values.size()!=DEFAULT.size() || new HashSet<>(values).size()!=DEFAULT.size()
            || !new HashSet<>(values).equals(new HashSet<>(DEFAULT)))return defaults();
        return new HomeMenuOrder(values);
    }
    public HomeMenuOrder copy(){return new HomeMenuOrder(ids);}
    public int size(){return ids.size();}
    public String get(int index){return ids.get(index);}
    public int indexOf(String id){return ids.indexOf(id);}
    public List<String> snapshot(){return Collections.unmodifiableList(new ArrayList<>(ids));}
    public String serialize(){return String.join(",",ids);}
    public boolean move(String id,int destination){
        int from=ids.indexOf(id);
        if(from<0 || destination<0 || destination>=ids.size() || from==destination)return false;
        ids.remove(from);ids.add(destination,id);return true;
    }
}
