package org.roarin.kyocerakeypad.core;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;

/**
 * WQB430: in-memory playlist Move Mode. Nothing here writes state or touches audio.
 * A selected track is identified by its stable media key, never its display title.
 *
 * If changing this contract, also check KeypadPlayerActivity.saveMoveMode(),
 * StateMutation's atomic writer, and service playback-order refresh.
 */
public final class PlaylistReorderDraft {
    private final String playlistId;
    private final String selectedKey;
    private final ArrayList<String> original;
    private final ArrayList<String> order;

    public PlaylistReorderDraft(String playlistId, List<String> entries, String selectedKey) {
        if(playlistId==null || playlistId.isEmpty() || entries==null || selectedKey==null ||
                !entries.contains(selectedKey) || new HashSet<>(entries).size()!=entries.size())
            throw new IllegalArgumentException("Cannot start playlist Move Mode");
        this.playlistId=playlistId;
        this.selectedKey=selectedKey;
        this.original=new ArrayList<>(entries);
        this.order=new ArrayList<>(entries);
    }
    public String playlistId(){return playlistId;}
    public String selectedKey(){return selectedKey;}
    public int selectedIndex(){return order.indexOf(selectedKey);}
    public int originalIndex(){return original.indexOf(selectedKey);}
    public int size(){return order.size();}
    public boolean changed(){return !order.equals(original);}
    public List<String> snapshot(){return new ArrayList<>(order);}
    public boolean matchesCurrent(List<String> entries){return original.equals(entries);}
    public boolean moveBy(int step){
        if(step!=1 && step!=-1)throw new IllegalArgumentException("Only one step allowed");
        return moveTo(selectedIndex()+step);
    }
    public boolean moveTop(){return moveTo(0);}
    public boolean moveBottom(){return moveTo(order.size()-1);}
    private boolean moveTo(int to){
        int from=selectedIndex();
        if(to<0 || to>=order.size() || from==to)return false;
        order.add(to,order.remove(from));
        return true;
    }
    /**
     * Apply once to a copy in StateMutation.prepareAndSave. Refuse stale playlist
     * contents rather than silently overwriting additions/removals since entry.
     */
    public void apply(PlayerState target){
        PlayerState.Playlist p=target.getPlaylist(playlistId);
        if(!p.entries.equals(original))
            throw new IllegalStateException("Playlist changed during Move Mode; cancel and reopen");
        if(!changed())return;
        p.entries.clear();
        p.entries.addAll(order);
    }
}
