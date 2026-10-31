package org.roarin.kyocerakeypad.core;

import java.util.ArrayList;
import java.util.List;

/** Read-only Now Playing labels and bookmark navigation; never edits playlist order. */
public final class NowPlayingNavigation {
    private NowPlayingNavigation() {}
    public static final class Neighbors {
        public final String previousKey, nextKey;
        public final boolean sessionShuffleOrder;
        Neighbors(String previous, String next, boolean shuffle) {
            previousKey=previous;nextKey=next;sessionShuffleOrder=shuffle;
        }
    }
    /** Session shuffle order is displayed only when it still matches saved identities. */
    public static Neighbors neighbors(List<String> saved, List<String> session,
                                      String current, boolean shuffle, boolean wrap) {
        if(saved==null || current==null || !saved.contains(current))
            return new Neighbors(null,null,false);
        boolean sessionValid=shuffle && session!=null && session.size()==saved.size()
            && session.containsAll(saved) && saved.containsAll(session);
        // A stale shuffle order must not pretend saved order predicts the next skip:
        // the service will re-shuffle when it notices the playlist changed.
        if(shuffle && !sessionValid)return new Neighbors(null,null,false);
        List<String> order=sessionValid?session:saved;
        int index=order.indexOf(current);
        if(index<0)return new Neighbors(null,null,false);
        int size=order.size();
        String previous=index>0?order.get(index-1):(wrap && size>1?order.get(size-1):null);
        String next=index<size-1?order.get(index+1):(wrap && size>1?order.get(0):null);
        return new Neighbors(previous,next,sessionValid);
    }
    /** Returns a bookmark INDEX, not its name or timestamp; strict inequalities skip the current mark. */
    public static int bookmarkIndex(List<PlayerState.Bookmark> marks,String trackKey,long positionMs,
                                    int direction) {
        if(marks==null || trackKey==null || (direction!=1 && direction!=-1))return -1;
        int chosen=-1;long best=direction>0?Long.MAX_VALUE:Long.MIN_VALUE;
        for(int i=0;i<marks.size();i++){
            PlayerState.Bookmark mark=marks.get(i);
            if(!trackKey.equals(mark.trackKey))continue;
            if(direction>0 && mark.positionMs>positionMs && mark.positionMs<best){best=mark.positionMs;chosen=i;}
            if(direction<0 && mark.positionMs<positionMs && mark.positionMs>best){best=mark.positionMs;chosen=i;}
        }
        return chosen;
    }
}
