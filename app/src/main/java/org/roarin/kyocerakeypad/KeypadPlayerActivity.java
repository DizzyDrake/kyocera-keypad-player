package org.roarin.kyocerakeypad;

import android.Manifest;
import android.app.*;
import android.os.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.media.MediaPlayer;
import android.media.AudioManager;
import android.media.AudioAttributes;
import android.media.AudioFocusRequest;
import android.net.Uri;
import android.provider.MediaStore;
import android.util.AtomicFile;
import android.view.*;
import android.view.inputmethod.EditorInfo;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.widget.*;
import org.roarin.kyocerakeypad.core.PlayerState;
import org.roarin.kyocerakeypad.core.StateCodec;
import org.roarin.kyocerakeypad.core.PlaybackGate;
import org.roarin.kyocerakeypad.core.AudioFocusGate;
import org.roarin.kyocerakeypad.core.CompletionPolicy;
import org.roarin.kyocerakeypad.core.PhoneSnapshotExport;
import org.roarin.kyocerakeypad.core.PhonePlaylistImport;
import org.json.*;
import java.nio.charset.StandardCharsets;
import org.roarin.kyocerakeypad.core.AlphabetJump;
import org.roarin.kyocerakeypad.core.StateMutation;
import org.roarin.kyocerakeypad.core.FailedOpenRollback;
import org.roarin.kyocerakeypad.core.NowPlayingNavigation;
import org.roarin.kyocerakeypad.core.PlaylistReorderDraft;
import org.roarin.kyocerakeypad.core.HomeMenuOrder;
import java.io.*;
import java.util.*;

/**
 * WQB405 SOURCE-ONLY service-integration prototype. Native focusable lists; real
 * E4831 keypad, viewport, playback and lifecycle behavior have NOT been tested.
 */
public final class KeypadPlayerActivity extends Activity {
    private static final int PERMISSION_REQUEST=29;
    // Service is the only owner of PlayerState, AtomicFile, MediaPlayer and focus.
    private PlayerState state;
    private KeypadPlaybackService playback;
    private boolean bound;
    private boolean recoveryMode=false, mediaReady=false, activeBook=false;
    private final Set<String> missing=new HashSet<>(), conflicts=new HashSet<>();
    private final Map<String,String> mediaPaths=new HashMap<>();
    private final KeypadPlaybackService.Listener playbackListener=new KeypadPlaybackService.Listener(){
        @Override public void onPlaybackChanged(){
            if(playback==null)return;
            state=playback.state;activeBook=playback.activeBook;
            if(previewPlayer!=null && !playback.previewFocusGranted())stopPreview();
            if("NOW".equals(screen)) {
                // Preserve the selected D-pad action on periodic playback updates.
                // If Now Playing rows change, also review selection identity.
                int selected = list.getSelectedItemPosition();
                showNow();
                if (selected >= 0 && selected < labels.size()) list.setSelection(selected);
            }
        }
        @Override public void onPlaybackError(String error){
            if(!isFinishing())message(error);
        }
    };
    private final ServiceConnection serviceConnection=new ServiceConnection(){
        @Override public void onServiceConnected(ComponentName name,IBinder binder){
            playback=((KeypadPlaybackService.LocalBinder)binder).service();bound=true;
            state=playback.state;recoveryMode=playback.recoveryMode;
            activeBook=playback.activeBook;playback.setListener(playbackListener);
            if(recoveryMode){
                heading.setText("Saved state needs recovery");
                footer.setText("Preserve app data. Do not clear storage.");
                list.setAdapter(new ArrayAdapter<>(KeypadPlayerActivity.this,
                    android.R.layout.simple_list_item_1,
                    new String[]{"Cannot safely open saved playlists. Press Back to exit."}));
            }else{
                showHome();
                if(checkSelfPermission(Manifest.permission.READ_EXTERNAL_STORAGE)==PackageManager.PERMISSION_GRANTED)scanLibrary();
                else requestPermissions(new String[]{Manifest.permission.READ_EXTERNAL_STORAGE},PERMISSION_REQUEST);
            }
        }
        @Override public void onServiceDisconnected(ComponentName name){
            playback=null;state=null;moveDraft=null;actions.clear();labels.clear();
            heading.setText("Playback connection lost");footer.setText("No automatic restart. Reopen when safe.");
            list.setAdapter(new ArrayAdapter<>(KeypadPlayerActivity.this,
                android.R.layout.simple_list_item_1,new String[]{"Playback unavailable; press Back to exit."}));
        }
    };
    private final Handler timer=new Handler();
    private String screen="HOME", selectedPlaylist="", selectedTrack="", libraryFilter="";
    private boolean adding=false, browsingBook=false;
    private TextView heading, footer;
    private MediaPlayer previewPlayer; // Isolated audition: never writes music/book progress.
    private boolean previewPrepared=false, previewRequested=false;
    private String previewTrackKey="", libraryTrackKey="";
    private int libraryTrackSelection=0;
    // Row identity for D-pad RIGHT Play Playlist shortcut (row 0 is Create).
    private final ArrayList<String> playlistRowIds=new ArrayList<>();
    private ListView list;
    private final ArrayList<Runnable> actions=new ArrayList<>();
    private final ArrayList<String> labels=new ArrayList<>();
    private final ArrayList<String> visibleLibraryTitles=new ArrayList<>();
    private int libraryReturnSelection=0;
    // Move Mode is a transient draft, not an edit of the playback service's state.
    // If this UI is changed, preserve explicit save/cancel and the selected track key.
    private PlaylistReorderDraft moveDraft;
    // Separate app-private UI preference; never mutates playback playlists/progress.
    private HomeMenuOrder homeOrder=HomeMenuOrder.defaults(), homeDraft;
    private String homeMovingId="";
    private int detailTrackStartRow=-1;
    private long lastPersistAt=0L;

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        homeOrder=HomeMenuOrder.parse(getSharedPreferences("dumbplayer_home_menu",MODE_PRIVATE)
            .getString("order", ""));
        LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);
        box.setBackgroundColor(Color.parseColor("#F5F0EB"));
        heading=new TextView(this);heading.setTextSize(19);heading.setPadding(12,9,12,9);
        heading.setTextColor(Color.WHITE);heading.setBackgroundColor(Color.parseColor("#713E46"));
        footer=new TextView(this);footer.setTextSize(15);footer.setPadding(12,8,12,8);
        footer.setTextColor(Color.parseColor("#252022"));footer.setBackgroundColor(Color.parseColor("#E9DCD8"));
        list=new ListView(this);list.setChoiceMode(ListView.CHOICE_MODE_SINGLE);
        list.setBackgroundColor(Color.parseColor("#F5F0EB"));
        list.setSelector(new ColorDrawable(Color.parseColor("#D6A6AD")));
        box.addView(heading);box.addView(list,new LinearLayout.LayoutParams(-1,0,1));box.addView(footer);
        setContentView(box);
        list.setOnItemClickListener((parent,view,pos,id)->{if(pos>=0 && pos<actions.size())actions.get(pos).run();});
        heading.setText("Loading playback state");
        footer.setText("Connecting to local playback service · no autoplay");
        bound=bindService(new Intent(this,KeypadPlaybackService.class),serviceConnection,Context.BIND_AUTO_CREATE);
        if(!bound){heading.setText("Playback service unavailable");footer.setText("No changes made. Reopen when safe.");}
        timer.postDelayed(tick,2000);
    }
    private final Runnable tick=new Runnable(){@Override public void run(){
        if(playback!=null && "NOW".equals(screen))footer.setText(nowFooter());
        timer.postDelayed(this,2000);
    }};
    private static String clock(long ms){long s=Math.max(0,ms)/1000;return String.format(Locale.US,"%02d:%02d:%02d",s/3600,(s/60)%60,s%60);}
    private void render(String title,String hint){
        heading.setTextSize("NOW".equals(screen)?16:19);
        footer.setTextSize("NOW".equals(screen)?13:15);
        heading.setText(title);footer.setText(hint);
        list.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_list_item_1,labels){
            @Override public View getView(int position,View convert,android.view.ViewGroup parent){
                TextView t=(TextView)super.getView(position,convert,parent);
                t.setTextSize(18);t.setTextColor(Color.parseColor("#252022"));
                t.setSingleLine(false);t.setMaxLines(4);t.setPadding(12,12,12,12);
                return t;
            }
        });
        list.setItemsCanFocus(false);list.setSelection(0);list.requestFocus();
    }
    private void reset(String newScreen){screen=newScreen;labels.clear();actions.clear();}
    private void item(String label,Runnable action){labels.add(label);actions.add(action);}
    private String homeLabel(String id){
        switch(id){
            case "resume_music":return "Resume music (explicit play)";
            case "resume_audiobook":return "Resume audiobook (explicit play)";
            case "music_playlists":return "Music playlists";
            case "audiobook_playlists":return "Audiobook playlists";
            case "browse_audio":return "Browse / search local audio";
            case "listening_settings":return "Listening settings";
            case "export_metadata":return "Export metadata for PC (manual)";
            case "help":return "Help / controls";
            case "about":return "About / version";
            default:throw new IllegalArgumentException("Unknown home action: "+id);
        }
    }
    private void homeAction(String id){
        switch(id){
            case "resume_music":resume(false);break;
            case "resume_audiobook":resume(true);break;
            case "music_playlists":showPlaylists(false);break;
            case "audiobook_playlists":showPlaylists(true);break;
            case "browse_audio":showLibrary(false);break;
            case "listening_settings":showSettings();break;
            case "export_metadata":confirmMetadataExport();break;
            case "help":showHelp();break;
            case "about":showAbout();break;
        }
    }
    private void showHome(){
        reset("HOME");
        for(int i=0;i<homeOrder.size();i++){
            final String id=homeOrder.get(i);
            item((i+1)+". "+homeLabel(id),()->homeAction(id));
        }
        render("Dumbplayer · DEV10 import trial",
            (mediaReady?"D-pad selects · Center opens":"Audio permission needed for playback")+
            " · 1–9 opens saved menu positions · * Reorder");
    }
    /** Provisional * binding, not a selected owner key; no tenth menu entry. */
    private void startHomeReorder(){
        int row=list.getSelectedItemPosition();
        if(row<0 || row>=homeOrder.size())row=0;
        homeDraft=homeOrder.copy();homeMovingId=homeDraft.get(row);
        showHomeReorder();
    }
    private void showHomeReorder(){
        if(homeDraft==null){showHome();return;}
        final HomeMenuOrder draft=homeDraft;
        reset("HOME_REORDER");
        for(int i=0;i<draft.size();i++){
            final String id=draft.get(i);
            item((id.equals(homeMovingId)?"> MOVING ":"  ")+(i+1)+". "+homeLabel(id),()->{});
        }
        render("Reorder main menu", "Up/Down move · 1 Top · 9 Bottom · Center Save · CLR Cancel");
        int row=draft.indexOf(homeMovingId);
        list.post(()->{if("HOME_REORDER".equals(screen) && homeDraft==draft &&
            draft.indexOf(homeMovingId)==row){
            // Ignore an older queued selection callback after another rapid move.
            list.setSelection(row);list.requestFocus();
        }});
    }
    private void homeMove(int key){
        if(homeDraft==null)return;
        int current=homeDraft.indexOf(homeMovingId);
        int destination=current;
        switch(key){
            case KeyEvent.KEYCODE_DPAD_UP:destination=Math.max(0,current-1);break;
            case KeyEvent.KEYCODE_DPAD_DOWN:destination=Math.min(homeDraft.size()-1,current+1);break;
            case KeyEvent.KEYCODE_1:destination=0;break;
            case KeyEvent.KEYCODE_9:destination=homeDraft.size()-1;break;
        }
        if(homeDraft.move(homeMovingId,destination))showHomeReorder();
    }
    private void finishHomeReorder(boolean save){
        final String selected=homeMovingId;
        if(save && homeDraft!=null){
            // Commit synchronously; a failed write must not pretend the new order is durable.
            boolean persisted=getSharedPreferences("dumbplayer_home_menu",MODE_PRIVATE).edit()
                .putString("order",homeDraft.serialize()).commit();
            if(!persisted){message("Menu order not saved; retry or cancel.");return;}
            homeOrder=homeDraft.copy();
        }
        homeDraft=null;homeMovingId="";showHome();
        int row=homeOrder.indexOf(selected);
        if(row>=0)list.post(()->{if("HOME".equals(screen))list.setSelection(row);});
    }
    private void showAbout(){
        // BUILD_UTC is generated by Gradle configuration on the builder's machine.
        // No build timestamp is invented for an uncompiled source-only ZIP.
        message("Dumbplayer · DISPOSABLE SANDBOX\nApplication ID: "+getPackageName()+"\nVersion: "+BuildConfig.VERSION_NAME+
            "\nBuild configured UTC: "+BuildConfig.BUILD_UTC+
            "\nSource candidate prepared: 2026-11-06"+
            "\nRelease date: Not released"+
            "\nDEV11 opt-in Bluetooth diagnostic source; real headset input test not certified."+
            "\nMade by GPT-6 and Aurora Williamsen"+
            "\nOffline player · No cloud upload");
    }
    private void showHelp(){
        reset("HELP");item("Back to home",this::showHome);
        item("Home menu: reorder and digits 1–9",()->message("On Home, highlight an entry and press * (provisional shortcut) to move it. Up/Down reorders, 1/9 jumps to top/bottom, Center saves, CLR cancels. On Home, digits 1–9 open the entries at their saved positions."));
        item("Playlists: select an item to reorder or remove",()->message("Highlight a playlist track and press * to move it in place. D-pad Up/Down moves it, 1/9 jumps to top/bottom, Center saves and CLR cancels. Track actions also opens Move Mode. Order is never alphabetized."));
        item("Now playing: seek 10 seconds or bookmark",()->message("Music and audiobook progress are separate. No autoplay on launch."));
        item("About / version",this::showAbout);
        item("Listening settings",this::showSettings);
        item("Experimental double NEXT = +10s: "+(playback!=null && playback.experimentalDoubleNext()?"ON":"OFF"),()->{
            if(playback!=null){playback.setExperimentalDoubleNext(!playback.experimentalDoubleNext());showHelp();}
        });
        item("Headset shortcut explanation",()->message("Optional experiment only: two NEXT media events within 350 ms seek +10 seconds. Single NEXT is delayed 350 ms while enabled. Your headset TAP is Volume Down; HOLD is Next. Double Volume Down may not reach this app. Leave OFF if uncertain."));
        item("Safety / limitations",()->message("EXISTING SANDBOX UPDATE. This build uses the same app-private playlists and progress as the previous WQA365 sandbox when updated in place; it stays separate from the original player. Use disposable test media. No cloud. Do not uninstall either app to resolve signing problems. MediaStore IDs can change; missing/changed files are blocked."));
        render("Help","D-pad Up/Down · Center selects · Playlist RIGHT = Play · Headset trial pending.");
    }
    private void showSettings(){
        reset("SETTINGS");
        item("Audiobook resume rewind: "+(playback==null?"Off":rewindLabel(playback.audiobookRewindSeconds())),()->{
            if(playback!=null){playback.cycleAudiobookRewind();showSettings();}
        });
        item("Import PC playlists (ADB transfer)",this::confirmPlaylistImport);
        item("Record Bluetooth volume/keys (45s)",()->{
            if(playback==null){message("Playback service unavailable");return;}
            if(!playback.isPlaying()){
                message("Start a track playing first, then start this 45-second diagnostic.");return;
            }
            if(playback.startBluetoothDiagnostic()){
                message("Bluetooth diagnostic started for 45 seconds. You can close the flip. Press one Volume Up, two quick Up, one Down, two quick Down, then optionally Hold Next. It saves a small bt_probe_*.txt in the existing transfer folder. No controls are remapped.");
            }else message("Bluetooth diagnostic already running, or audio service unavailable.");
        });
        item("Sleep timer: set from Music or Audiobook Now Playing",()->message(
            "Start or resume a track, then choose Sleep timer in Now Playing. It pauses and saves the position."));
        item("← Home",this::showHome);
        render("Listening settings","Rewind: Off / 5s / 10s · Off is default · no autoplay");
    }
    private static String rewindLabel(int seconds){return seconds==0?"Off":seconds+" seconds";}
    private String sleepTimerLabel(){
        if(playback==null || !playback.sleepTimerArmed())return "Off";
        long ms=playback.sleepTimerRemainingMs();
        return (ms/60000L+(ms%60000L>0?1:0))+"m left";
    }
    private void showSleepTimerOptions(){
        if(playback==null || !playback.isPrepared()){message("Start a track first");return;}
        String[] options={"Off / Cancel", "10 minutes", "15 minutes", "30 minutes", "60 minutes", "Custom minutes"};
        new AlertDialog.Builder(this).setTitle("Sleep timer · "+sleepTimerLabel())
            .setItems(options,(dialog,which)->{
                if(playback==null)return;
                if(which==0){playback.cancelSleepTimer();showNow();return;}
                if(which==5){promptSleepTimerMinutes();return;}
                int[] presets={0,10,15,30,60};
                if(which>0 && which<5){playback.setSleepTimerMinutes(Integer.toString(presets[which]));showNow();}
            }).setNegativeButton("Back",(d,w)->{}).show();
    }
    private void promptSleepTimerMinutes(){
        EditText input=new EditText(this);
        input.setSingleLine(true);
        input.setInputType(android.text.InputType.TYPE_CLASS_NUMBER);
        input.setHint("Positive whole minutes");
        AlertDialog dialog=new AlertDialog.Builder(this).setTitle("Custom sleep timer (minutes)")
            .setView(input).setNegativeButton("Cancel",(d,w)->{})
            .setPositiveButton("Set",null).create();
        dialog.setOnShowListener(d->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{
            String minutes=input.getText().toString().trim();
            try { org.roarin.kyocerakeypad.core.SleepTimerPolicy.durationMs(minutes); }
            catch(IllegalArgumentException e){input.setError(e.getMessage());return;}
            if(playback!=null && playback.setSleepTimerMinutes(minutes)){dialog.dismiss();showNow();}
        }));
        dialog.show();
    }
    private void showPlaylists(boolean book){
        browsingBook=book;reset("PLAYLISTS");playlistRowIds.clear();playlistRowIds.add("");
        item("+ Create playlist",()->prompt("Playlist name","",name->{
            String id=UUID.randomUUID().toString();
            if(commitMutation("Create playlist",next->next.createPlaylist(id,name,book))){
                selectedPlaylist=id;showDetail();
            }
        }));
        for(PlayerState.Playlist p:state.playlists.values())if(p.audiobook==book){
            playlistRowIds.add(p.id);
            item(p.name+" ("+p.entries.size()+" tracks)",()->{selectedPlaylist=p.id;showDetail();});
        }
        item("← Back",this::showHome);
        render(book?"Audiobook playlists":"Music playlists","Center opens playlist · RIGHT plays highlighted playlist · no autoplay");
    }
    private void showDetail(){
        PlayerState.Playlist p=state.playlists.get(selectedPlaylist);
        if(p==null){showPlaylists(browsingBook);return;}
        browsingBook=p.audiobook;reset("DETAIL");
        item("▶ Play playlist",()->playPlaylist(p));
        item("Shuffle: "+(playback!=null && playback.shuffleEnabled()?"ON":"OFF"),()->{
            if(playback!=null){playback.setShuffle(!playback.shuffleEnabled());showDetail();}
        });
        item("Repeat: "+repeatLabel(),()->{
            if(playback!=null){playback.cycleRepeat();showDetail();}
        });
        item("+ Add track from library",()->{adding=true;showLibrary(p.audiobook);});
        item("Rename playlist",()->prompt("Rename playlist",p.name,name->{if(commitMutation("Rename playlist",next->next.renamePlaylist(p.id,name)))showDetail();}));
        item("Delete playlist",()->new AlertDialog.Builder(this).setTitle("Delete playlist?")
            .setMessage("The playlist is removed, but audio files remain untouched.")
            .setNegativeButton("Cancel",(d,w)->{}).setPositiveButton("Delete",(d,w)->{
                if(!stopPlayer()){
                    message("Cannot delete playlist until playback position is saved.");return;
                }
                if(commitMutation("Delete playlist",next->next.deletePlaylist(p.id)))showPlaylists(p.audiobook);
            }).show());
        detailTrackStartRow=labels.size();
        int i=0;
        for(String key:p.entries){final int idx=i++;PlayerState.Track t=state.tracks.get(key);
            String title=t==null?"[missing identity]":t.title;
            item(i+". "+title+((missing.contains(key)||conflicts.contains(key))?" [unavailable]":""),()->{
                selectedTrack=key;showTrackActions(idx);
            });
        }
        item("← Playlists",()->showPlaylists(p.audiobook));
        render(p.name,"* on track = Move Mode · RIGHT plays playlist · Center selects");
    }
    private String repeatLabel(){
        if(playback==null)return "Off";
        switch(playback.repeatMode()){
            case PLAYLIST:return "Repeat Playlist";
            case TRACK:return "Repeat Track";
            default:return "Off";
        }
    }
    private void playPlaylist(PlayerState.Playlist p){
        stopPreview();
        if(playback==null || !mediaReady){message("Audio service/library not ready");return;}
        if(p.entries.isEmpty()){message("Add tracks before playing this playlist");return;}
        // Existing foreground service starts only for a deliberate Play action.
        startForegroundService(new Intent(this,KeypadPlaybackService.class));
        if(!playback.playPlaylist(p.id)){message(playback.lastError());return;}
        state=playback.state;activeBook=playback.activeBook;showNow();
    }
    private void showTrackActions(int index){
        PlayerState.Playlist p=state.getPlaylist(selectedPlaylist);
        if(index<0 || index>=p.entries.size()){showDetail();return;}
        String key=p.entries.get(index);PlayerState.Track t=state.tracks.get(key);
        reset("TRACK_ACTIONS");
        item("Play this track",()->playFrom(p,index,false));
        item("Move in playlist (keypad Move Mode)",()->startMoveMode(index));
        item("Remove from playlist (audio kept)",()->{commitMutation("Remove track",next->next.remove(p.id,index));showDetail();});
        item("← Back",this::showDetail);
        render(t==null?"Missing track":t.title,"Select action. Reordering never changes the audio file.");
    }
    /** Enter an in-list reorder draft; no playlist mutation until Center/save. */
    private void startMoveMode(int index){
        PlayerState.Playlist p=state==null?null:state.playlists.get(selectedPlaylist);
        if(p==null || index<0 || index>=p.entries.size()){
            message("Playlist track no longer available");return;
        }
        try{moveDraft=new PlaylistReorderDraft(p.id,p.entries,p.entries.get(index));}
        catch(IllegalArgumentException e){message("Cannot start Move Mode: "+e.getMessage());return;}
        showMoveMode();
    }
    private void showMoveMode(){
        final PlaylistReorderDraft draft=moveDraft;
        if(draft==null){showDetail();return;}
        reset("MOVE");
        List<String> order=draft.snapshot();
        for(int i=0;i<order.size();i++){
            String key=order.get(i);
            PlayerState.Track track=state==null?null:state.tracks.get(key);
            String title=track==null?"[missing track identity]":track.title;
            final boolean moving=key.equals(draft.selectedKey());
            item((moving?"> MOVING ":"  ")+(i+1)+". "+title,()->{
                // Touching a row does not accidentally change the picked-up track.
                // Center is reserved for saving; CLR cancels the entire draft.
            });
        }
        render("Move track · "+(draft.selectedIndex()+1)+"/"+draft.size(),
            "Up/Down move · 1 Top · 9 Bottom · Center Save · CLR Cancel"+
            (draft.changed()?" · unsaved":""));
        final int selected=draft.selectedIndex();
        list.post(()->{if("MOVE".equals(screen) && moveDraft==draft){
            list.setSelectionFromTop(selected,Math.max(0,list.getHeight()/3));list.requestFocus();
        }});
    }
    private void moveByKey(int key){
        if(moveDraft==null)return;
        boolean moved=false;
        switch(key){
            case KeyEvent.KEYCODE_DPAD_UP:moved=moveDraft.moveBy(-1);break;
            case KeyEvent.KEYCODE_DPAD_DOWN:moved=moveDraft.moveBy(1);break;
            case KeyEvent.KEYCODE_1:moved=moveDraft.moveTop();break;
            case KeyEvent.KEYCODE_9:moved=moveDraft.moveBottom();break;
        }
        if(moved)showMoveMode();
    }
    private void leaveMoveMode(){
        PlaylistReorderDraft draft=moveDraft;
        moveDraft=null;
        if(draft==null){showDetail();return;}
        selectedPlaylist=draft.playlistId();
        showDetail();
        final int row=detailTrackStartRow+Math.max(0,
            state.getPlaylist(selectedPlaylist).entries.indexOf(draft.selectedKey()));
        list.post(()->{if("DETAIL".equals(screen)){
            list.setSelection(Math.min(row,labels.size()-1));list.requestFocus();
        }});
    }
    private void cancelMoveMode(){leaveMoveMode();}
    private void saveMoveMode(){
        final PlaylistReorderDraft draft=moveDraft;
        if(draft==null)return;
        if(!draft.changed()){leaveMoveMode();return;}
        // StateMutation prepares a copy and writes once. If another edit changed
        // the saved entry list, draft.apply also rejects it inside that copy.
        PlayerState.Playlist current=state==null?null:state.playlists.get(draft.playlistId());
        if(current==null || !draft.matchesCurrent(current.entries)){
            message("Playlist changed while moving. Cancel and reopen to avoid losing edits.");return;
        }
        if(!commitMutation("Save playlist order",draft::apply))return;
        // A non-shuffled active session must follow the newly saved order without
        // restarting audio or altering current track/position. Shuffle stays session-only.
        if(playback!=null)playback.onPlaylistOrderSaved(draft.playlistId());
        leaveMoveMode();
    }

    private void showLibrary(boolean book){
        browsingBook=book;reset("LIBRARY");
        visibleLibraryTitles.clear();
        item("Filter by title / artist / album / folder",()->prompt("Search local audio",libraryFilter,text->{libraryFilter=text;showLibrary(book);}));
        String f=libraryFilter.toLowerCase(Locale.ROOT);
        ArrayList<PlayerState.Track> sorted=new ArrayList<>(state.tracks.values());
        sorted.sort((a,b)->a.title.compareToIgnoreCase(b.title));
        for(PlayerState.Track t:sorted){
            String hay=(t.title+" "+t.artist+" "+t.album+" "+t.folder).toLowerCase(Locale.ROOT);
            if(!hay.contains(f))continue;
            visibleLibraryTitles.add(t.title);
            item(t.title+" — "+t.artist+" / "+t.album+(missing.contains(t.key)?" [missing]":conflicts.contains(t.key)?" [changed]":""),()->{
                libraryTrackSelection=Math.max(0,list.getSelectedItemPosition());
                showLibraryTrackActions(t.key);
            });
        }
        item("← Back",()->{if(adding){adding=false;showDetail();}else showHome();});
        render("Local audio library","Right: A-Z title jump · Up/Down: tracks · Center: select · CLR: back");
    }
    private void showLibraryTrackActions(String key){
        PlayerState.Track t=state.tracks.get(key);
        if(t==null){showLibrary(browsingBook);return;}
        libraryTrackKey=key;
        reset("LIBRARY_TRACK");
        if(adding){
            item("+ Add to selected playlist",()->{
                try{
                    // Keep the current selected playlist and all playback positions intact.
                    if(!addTrackAndPersist(selectedPlaylist,key))return;
                    adding=false;showDetail();
                }catch(IllegalArgumentException e){message(e.getMessage());}
            });
        } else item("+ Choose playlist to add",()->choosePlaylistForLibraryTrack(key));
        item("▶ Preview / Play (no playlist change)",()->startPreview(key));
        item("← Back to library",this::returnToLibrary);
        render(t.title,"Center selects · Preview is temporary · CLR returns");
    }
    private boolean addTrackAndPersist(String playlistId,String key){
        if(missing.contains(key) || conflicts.contains(key)){
            message("Cannot add a missing or changed audio identity. Review library first.");
            return false;
        }
        state.add(playlistId,key);
        if(persist())return true;
        // Restore the in-memory entry if AtomicFile could not commit.
        // Otherwise a later unrelated successful save could commit a failed add.
        PlayerState.Playlist p=state.getPlaylist(playlistId);
        p.entries.remove(key);
        message("Add could not be saved. No playlist change retained; review storage before retry.");
        return false;
    }
    private void choosePlaylistForLibraryTrack(String key){
        reset("LIBRARY_ADD");
        int count=0;
        for(PlayerState.Playlist p:state.playlists.values()){
            count++;
            item("+ "+p.name+(p.audiobook?" [book]":" [music]"),()->{
                try{
                    if(!addTrackAndPersist(p.id,key))return;
                    selectedPlaylist=p.id;showDetail();
                }catch(IllegalArgumentException e){message(e.getMessage());}
            });
        }
        if(count==0)item("No playlists yet · create one first",()->message("Create a playlist from Home, then return to the library."));
        item("← Track actions",()->showLibraryTrackActions(key));
        render("Choose destination playlist","Previewing does not add or change listening progress");
    }
    private void returnToLibrary(){
        showLibrary(browsingBook);
        selectLibraryPosition(libraryTrackSelection);
    }
    private void returnFromPreview(){
        stopPreview();
        showLibraryTrackActions(libraryTrackKey);
    }
    private void startPreview(String key){
        if(!mediaReady || !state.tracks.containsKey(key) || missing.contains(key) || conflicts.contains(key)){
            message("Preview blocked: track missing, changed or audio permission unavailable.");return;
        }
        // Stop and durably save the previous normal session before audition.
        // Preview itself NEVER selects a music/audiobook session or persists its playhead.
        stopPreview();
        if(!stopPlayer()){
            message("Cannot safely save previous playback. Preview was not started.");return;
        }
        if(!requestAudioFocusForExplicitPlay(false)){
            message("Preview unavailable during a call or other audio interruption.");return;
        }
        previewTrackKey=key;
        previewRequested=true;
        previewPrepared=false;
        MediaPlayer audition=new MediaPlayer();
        previewPlayer=audition;
        try{
            audition.setAudioAttributes(mediaAttributes(false));
            audition.setDataSource(this,Uri.parse(state.tracks.get(key).uri));
            audition.setOnPreparedListener(mp->{
                if(previewPlayer!=mp)return;
                previewPrepared=true;
                if(previewRequested && playback!=null && playback.previewFocusGranted())mp.start();
                if("PREVIEW".equals(screen))showPreview();
            });
            audition.setOnCompletionListener(mp->{
                if(previewPlayer!=mp)return;
                stopPreview();
                if("PREVIEW".equals(screen))showPreview();
            });
            audition.setOnErrorListener((mp,what,extra)->{
                if(previewPlayer!=mp)return true;
                stopPreview();message("Preview failed; original audio and saved progress unchanged.");return true;
            });
            audition.prepareAsync();
            showPreview();
        }catch(Exception e){
            stopPreview();message("Cannot preview track: "+e.getClass().getSimpleName());
        }
    }
    private void showPreview(){
        reset("PREVIEW");
        item("▶ Play / Pause preview",()->{
            if(previewPlayer==null){startPreview(previewTrackKey);return;}
            if(!previewPrepared){message("Preview is still preparing");return;}
            try{
                if(previewPlayer.isPlaying()){
                    previewRequested=false;previewPlayer.pause();abandonAudioFocus();
                }else if(requestAudioFocusForExplicitPlay(false)){
                    previewRequested=true;
                    if(playback!=null && playback.previewFocusGranted())previewPlayer.start();
                }else message("Preview unavailable during a call or other audio interruption.");
            }catch(IllegalStateException e){stopPreview();message("Preview player unavailable; retry explicitly.");}
            showPreview();
        });
        item("■ Stop preview",()->{stopPreview();showPreview();});
        item("← Track actions",this::returnFromPreview);
        PlayerState.Track t=state.tracks.get(previewTrackKey);
        render(t==null?"Preview":t.title,"Temporary audition · No playlist/bookmark changes · CLR stops");
    }
    private void stopPreview(){
        boolean hadPreview=previewPlayer!=null || previewRequested;
        previewRequested=false;
        previewPrepared=false;
        MediaPlayer old=previewPlayer;
        previewPlayer=null; // Detach first: stale async callbacks must be ignored.
        if(old!=null){
            try{old.reset();}catch(Exception ignored){}
            finally{try{old.release();}catch(Exception ignored){}}
        }
        if(hadPreview)abandonAudioFocus();
    }
    /** Source-only keypad mapping; actual E4831 key delivery still requires owner trial. */
    @Override public boolean dispatchKeyEvent(KeyEvent event) {
        int key=event.getKeyCode();
        // HOME numeric dispatch is positional and follows the saved user order.
        // Only HOME owns 1–9; Now Playing, playlist Move Mode and text fields are untouched.
        if("HOME".equals(screen) && !(getCurrentFocus() instanceof EditText)){
            if(key==KeyEvent.KEYCODE_STAR){
                if(event.getAction()==KeyEvent.ACTION_DOWN && event.getRepeatCount()==0)
                    startHomeReorder();
                return true;
            }
            if(key>=KeyEvent.KEYCODE_1 && key<=KeyEvent.KEYCODE_9){
                if(event.getAction()==KeyEvent.ACTION_DOWN && event.getRepeatCount()==0)
                    homeAction(homeOrder.get(key-KeyEvent.KEYCODE_1));
                return true;
            }
        }
        if("HOME_REORDER".equals(screen) && !(getCurrentFocus() instanceof EditText)){
            boolean move=key==KeyEvent.KEYCODE_DPAD_UP || key==KeyEvent.KEYCODE_DPAD_DOWN ||
                key==KeyEvent.KEYCODE_1 || key==KeyEvent.KEYCODE_9;
            boolean save=key==KeyEvent.KEYCODE_DPAD_CENTER || key==KeyEvent.KEYCODE_ENTER;
            boolean cancel=key==KeyEvent.KEYCODE_DEL || key==KeyEvent.KEYCODE_CLEAR ||
                key==KeyEvent.KEYCODE_BACK || key==KeyEvent.KEYCODE_ESCAPE;
            if(move || save || cancel){
                if(event.getAction()==KeyEvent.ACTION_DOWN){
                    if(move)homeMove(key);
                    else if(event.getRepeatCount()==0)finishHomeReorder(save);
                }
                return true;
            }
            // Ignore other digits in editing mode; never launch a home action.
            if(key>=KeyEvent.KEYCODE_0 && key<=KeyEvent.KEYCODE_9)return true;
        }
        // Move Mode owns D-pad moves (including key-repeat), top/bottom and
        // explicit save/cancel. Do not pass these keys to ListView navigation.
        if("MOVE".equals(screen) && !(getCurrentFocus() instanceof EditText)){
            boolean move=key==KeyEvent.KEYCODE_DPAD_UP || key==KeyEvent.KEYCODE_DPAD_DOWN ||
                key==KeyEvent.KEYCODE_1 || key==KeyEvent.KEYCODE_9;
            boolean save=key==KeyEvent.KEYCODE_DPAD_CENTER || key==KeyEvent.KEYCODE_ENTER;
            boolean cancel=key==KeyEvent.KEYCODE_DEL || key==KeyEvent.KEYCODE_CLEAR ||
                key==KeyEvent.KEYCODE_BACK || key==KeyEvent.KEYCODE_ESCAPE;
            if(move || save || cancel){
                if(event.getAction()==KeyEvent.ACTION_DOWN){
                    if(move)moveByKey(key); // deliberate repeats permit long-list movement
                    else if(event.getRepeatCount()==0){if(save)saveMoveMode();else cancelMoveMode();}
                }
                return true;
            }
        }
        // DETAIL * starts moving the highlighted track, not a command row.
        if("DETAIL".equals(screen) && key==KeyEvent.KEYCODE_STAR){
            if(event.getAction()==KeyEvent.ACTION_DOWN && event.getRepeatCount()==0){
                int index=list.getSelectedItemPosition()-detailTrackStartRow;
                PlayerState.Playlist p=state==null?null:state.playlists.get(selectedPlaylist);
                if(p!=null && index>=0 && index<p.entries.size())startMoveMode(index);
            }
            return true;
        }
        // Only Now Playing owns transport number-key shortcuts. Never intercept
        // edit fields, Library A-Z or repeated/UP events.
        if("NOW".equals(screen) && !(getCurrentFocus() instanceof EditText)) {
            boolean shortcut=key==KeyEvent.KEYCODE_1 || key==KeyEvent.KEYCODE_3 ||
                key==KeyEvent.KEYCODE_4 || key==KeyEvent.KEYCODE_5 ||
                key==KeyEvent.KEYCODE_6 || (activeBook &&
                (key==KeyEvent.KEYCODE_0 || key==KeyEvent.KEYCODE_7 ||
                 key==KeyEvent.KEYCODE_9 || key==KeyEvent.KEYCODE_POUND));
            if(shortcut){
                if(event.getAction()==KeyEvent.ACTION_DOWN && event.getRepeatCount()==0)
                    nowShortcut(key);
                return true;
            }
        }
        if (key==KeyEvent.KEYCODE_DPAD_RIGHT && "DETAIL".equals(screen)) {
            if(event.getAction()==KeyEvent.ACTION_DOWN && event.getRepeatCount()==0){
                PlayerState.Playlist p=state==null?null:state.playlists.get(selectedPlaylist);
                if(p!=null)playPlaylist(p);
            }
            return true;
        }
        if (key==KeyEvent.KEYCODE_DPAD_RIGHT && "PLAYLISTS".equals(screen)) {
            if(event.getAction()==KeyEvent.ACTION_DOWN && event.getRepeatCount()==0){
                int row=list.getSelectedItemPosition();
                if(row>0 && row<playlistRowIds.size()){
                    PlayerState.Playlist p=state.playlists.get(playlistRowIds.get(row));
                    if(p!=null)playPlaylist(p);
                }
            }
            return true;
        }
        if ("LIBRARY".equals(screen) && key==KeyEvent.KEYCODE_DPAD_RIGHT) {
            if(event.getAction()==KeyEvent.ACTION_DOWN && event.getRepeatCount()==0) showAlphabetIndex();
            return true; // consume repeats and UP, so one press opens one picker
        }
        if ("ALPHABET".equals(screen) && key==KeyEvent.KEYCODE_DPAD_LEFT) {
            if(event.getAction()==KeyEvent.ACTION_DOWN && event.getRepeatCount()==0) restoreLibrary();
            return true;
        }
        return super.dispatchKeyEvent(event);
    }
    private void showAlphabetIndex() {
        libraryReturnSelection=Math.max(0,list.getSelectedItemPosition());
        Map<Character,Integer> counts=AlphabetJump.counts(visibleLibraryTitles);
        reset("ALPHABET");
        for(Map.Entry<Character,Integer> entry:counts.entrySet()) {
            final char letter=entry.getKey();
            item(letter+" · "+entry.getValue()+" tracks",()->jumpToLibraryLetter(letter));
        }
        if(counts.isEmpty()) item("No tracks match current search",this::restoreLibrary);
        item("← Return to tracks",this::restoreLibrary);
        render("Jump to title · A-Z","Up/Down: choose letter · Center: jump · Left/CLR: return");
    }
    private void jumpToLibraryLetter(char letter) {
        showLibrary(browsingBook);
        int index=AlphabetJump.firstMatchingIndex(visibleLibraryTitles,letter);
        if(index>=0) selectLibraryPosition(index+1); // first row is typed-filter action
    }
    private void restoreLibrary() {
        showLibrary(browsingBook);
        selectLibraryPosition(libraryReturnSelection);
    }
    private void selectLibraryPosition(int position) {
        final int target=Math.max(0,Math.min(position,labels.size()-1));
        list.post(()->{if("LIBRARY".equals(screen)){
            list.setSelection(target);
            list.requestFocus();
        }});
    }
    private void prompt(String title,String initial,java.util.function.Consumer<String> onSave){
        EditText input=new EditText(this);
        input.setSingleLine(true);
        input.setImeOptions(EditorInfo.IME_ACTION_DONE);
        input.setText(initial);
        // Positive-button callbacks dismiss automatically, even on invalid input.
        // Attach the Save handler after show() so an empty name stays editable.
        final AlertDialog dialog=new AlertDialog.Builder(this).setTitle(title).setView(input)
            .setNegativeButton("Cancel",(d,w)->{})
            .setPositiveButton("Save",null).create();
        dialog.setOnShowListener(d->{
            final Button save=dialog.getButton(AlertDialog.BUTTON_POSITIVE);
            final Button cancel=dialog.getButton(AlertDialog.BUTTON_NEGATIVE);
            save.setOnClickListener(v->{
                String val=input.getText().toString().trim();
                if(val.isEmpty()){
                    input.setError("Name cannot be empty");
                    input.requestFocus();
                    return;
                }
                // Ignore a second IME/center event while the synchronous save runs.
                save.setEnabled(false);
                try{
                    onSave.accept(val);
                    dialog.dismiss();
                }catch(Exception e){
                    // Avoid a second tap repeating a partially completed state write.
                    dialog.dismiss();
                    message("Could not save: "+e.getMessage());
                }
            });
            // The E4831's edit field traps the usual Back/CLR keys as backspace.
            // Offer three explicit alternatives; actual key mapping still needs
            // owner-supervised device testing, not just a source-level assertion.
            input.setOnEditorActionListener((v,actionId,event)->{
                if(actionId==EditorInfo.IME_ACTION_DONE ||
                   (event!=null && event.getAction()==KeyEvent.ACTION_UP &&
                    (event.getKeyCode()==KeyEvent.KEYCODE_ENTER ||
                     event.getKeyCode()==KeyEvent.KEYCODE_NUMPAD_ENTER))){
                    save.performClick();return true;
                }
                return false;
            });
            input.setOnKeyListener((v,keyCode,event)->{
                if(keyCode==KeyEvent.KEYCODE_DPAD_CENTER){
                    if(event.getAction()==KeyEvent.ACTION_UP)save.performClick();
                    return true;
                }
                if(keyCode==KeyEvent.KEYCODE_DPAD_DOWN){
                    if(event.getAction()==KeyEvent.ACTION_UP)save.requestFocus();
                    return true;
                }
                if(keyCode==KeyEvent.KEYCODE_DPAD_UP){
                    if(event.getAction()==KeyEvent.ACTION_UP)cancel.requestFocus();
                    return true;
                }
                return false;
            });
            input.requestFocus();
        });
        dialog.show();
    }
    private void message(String s){new AlertDialog.Builder(this).setMessage(s).setPositiveButton("OK",(d,w)->{}).show();}
    private void scanLibrary(){
        if(recoveryMode)return;
        mediaReady=false;HashSet<String> seen=new HashSet<>();conflicts.clear();missing.clear();mediaPaths.clear();
        String[] columns={MediaStore.Audio.Media._ID,MediaStore.Audio.Media.TITLE,
            MediaStore.Audio.Media.ARTIST,MediaStore.Audio.Media.ALBUM,
            MediaStore.Audio.Media.DURATION,MediaStore.MediaColumns.SIZE,MediaStore.MediaColumns.RELATIVE_PATH,
            MediaStore.MediaColumns.DISPLAY_NAME};
        try(Cursor c=getContentResolver().query(MediaStore.Audio.Media.getContentUri(MediaStore.VOLUME_EXTERNAL),columns,null,null,null)){
            if(c==null){message("Cannot read audio library");return;}
            while(c.moveToNext()){
                long id=c.getLong(0);String uri=Uri.withAppendedPath(MediaStore.Audio.Media.getContentUri(MediaStore.VOLUME_EXTERNAL),Long.toString(id)).toString();
                String key=uri;seen.add(key);
                try{mediaPaths.put(key,PhoneSnapshotExport.relativePath(c.getString(6),c.getString(7)));}
                catch(IllegalArgumentException badPath){conflicts.add(key);}
                PlayerState.Track t=new PlayerState.Track(key,uri,c.getString(1),c.getString(2),c.getString(3),c.getString(6),c.getLong(4),c.getLong(5));
                PlayerState.Track old=state.tracks.get(key);
                if(old==null)state.tracks.put(key,t);
                else if(old.durationMs!=t.durationMs || old.sizeBytes!=t.sizeBytes ||
                        !old.title.equals(t.title) || !old.artist.equals(t.artist) ||
                        !old.album.equals(t.album) || !old.folder.equals(t.folder))conflicts.add(key);
            }
            for(String key:state.tracks.keySet())if(!seen.contains(key))missing.add(key);
            mediaReady=true;persist();showHome();
            if(!missing.isEmpty()||!conflicts.isEmpty())message("Some previously saved audio IDs are missing or changed. They will not play until reconciled; no automatic title-based substitutions.");
        }catch(Exception e){message("Audio scan failed: "+e.getClass().getSimpleName());}
    }
    /** Manual metadata-only ADB transfer: no audio, network or automatic import. */
    private void confirmMetadataExport(){
        if(recoveryMode || !mediaReady || !missing.isEmpty() || !conflicts.isEmpty()){
            message("Export blocked: audio scan incomplete, missing or changed tracks. No files exported.");return;
        }
        new AlertDialog.Builder(this).setTitle("Export metadata only?")
            .setMessage("Creates a local JSON snapshot of track names/paths, playlists, bookmarks and positions in this app's transfer folder. No audio copied. Filenames can be private. Use ADB only if you choose to later. Import is available under Listening settings after manual ADB transfer.")
            .setNegativeButton("Cancel",(d,w)->{})
            .setPositiveButton("Export",(d,w)->exportMetadata()).show();
    }
    private void exportMetadata(){
        if(recoveryMode || !mediaReady || !missing.isEmpty() || !conflicts.isEmpty()){
            message("Export blocked: library status changed.");return;
        }
        try {
            saveActivePosition();
            if(!persist())throw new IOException("Current player state could not be saved");
            byte[] json=PhoneSnapshotExport.encode(state,mediaPaths);
            File dir=getExternalFilesDir("transfer");
            if(dir==null || !dir.isDirectory())throw new IOException("Transfer folder unavailable");
            File dest=new File(dir,"phone_snapshot_"+UUID.randomUUID().toString()+".json");
            AtomicFile output=new AtomicFile(dest);
            FileOutputStream out=null;
            try{out=output.startWrite();out.write(json);output.finishWrite(out);}
            catch(Exception error){if(out!=null)output.failWrite(out);throw error;}
            message("Exported metadata only ("+json.length+" bytes) to: "+dest.getAbsolutePath()+"\nADB pull is owner-invoked. PC import requires separate confirmation.");
        } catch(Exception error) {
            message("Export refused/failed: "+error.getClass().getSimpleName()+" — "+error.getMessage());
        }
    }
    /** Read only the one known transfer filename; never browse other user files. */
    private void confirmPlaylistImport(){
        if(recoveryMode || playback==null || !mediaReady || !missing.isEmpty() || !conflicts.isEmpty()){
            message("Import blocked until the audio library is ready and consistent.");return;
        }
        File dir=getExternalFilesDir("transfer");
        if(dir==null){message("Transfer folder unavailable");return;}
        final File source=new File(dir,PhonePlaylistImport.FILENAME);
        if(!source.isFile()){message("No "+PhonePlaylistImport.FILENAME+" in transfer folder. Push it via ADB first.");return;}
        new AlertDialog.Builder(this).setTitle("Import PC playlists?")
            .setMessage("Replaces ALL playlists. Music/audiobook resume positions may reset if their playlist or track was removed. " +
                "Existing bookmarks and audio files stay in place. " +
                "The file must match the current phone snapshot; otherwise it is refused. Continue?")
            .setNegativeButton("Cancel",(d,w)->{})
            .setPositiveButton("Import",(d,w)->importPlaylists(source)).show();
    }
    private static String jsonText(JSONObject object,String name) throws JSONException {
        Object value=object.get(name);
        if(!(value instanceof String))throw new JSONException("Invalid "+name);
        return (String)value;
    }
    private void importPlaylists(File source){
        if(recoveryMode || playback==null || !mediaReady || !missing.isEmpty() || !conflicts.isEmpty()){
            message("Import blocked: audio library changed");return;
        }
        try{
            if(source.length()<=0 || source.length()>PhonePlaylistImport.MAX_BYTES)
                throw new IOException("Invalid import file size");
            // Exactly one bounded file, UTF-8; no implicit phone file chooser or network.
            ByteArrayOutputStream buf=new ByteArrayOutputStream();
            try(FileInputStream input=new FileInputStream(source)){
                byte[] block=new byte[8192];int n;
                while((n=input.read(block))!=-1){
                    if(buf.size()+n>PhonePlaylistImport.MAX_BYTES)throw new IOException("Oversize import");
                    buf.write(block,0,n);
                }
            }
            JSONObject payload=new JSONObject(new String(buf.toByteArray(),StandardCharsets.UTF_8));
            if(!PhonePlaylistImport.SCHEMA.equals(jsonText(payload,"schema")))
                throw new IOException("Unknown import format");
            String expected=jsonText(payload,"expected_snapshot_id");
            JSONArray ps=payload.getJSONArray("playlists");
            if(ps.length()>1000)throw new IOException("Too many playlists");
            ArrayList<PhonePlaylistImport.Spec> specs=new ArrayList<>();
            for(int i=0;i<ps.length();i++){
                JSONObject p=ps.getJSONObject(i);
                Object flag=p.get("audiobook");
                if(!(flag instanceof Boolean))throw new JSONException("Invalid audiobook flag");
                JSONArray rows=p.getJSONArray("track_keys");
                if(rows.length()>50000)throw new IOException("Too many playlist entries");
                ArrayList<String> keys=new ArrayList<>();
                for(int j=0;j<rows.length();j++){
                    Object entry=rows.get(j);
                    if(!(entry instanceof String))throw new JSONException("Invalid track identity");
                    keys.add((String)entry);
                }
                specs.add(new PhonePlaylistImport.Spec(jsonText(p,"id"),jsonText(p,"name"),
                    (Boolean)flag,keys));
            }
            // Stop and persist before the identity check: stopping active playback
            // may update the position and therefore the state-derived snapshot ID.
            if(!playback.stopPlayer())throw new IOException("Could not safely stop/save playback");
            String current=new JSONObject(new String(PhoneSnapshotExport.encode(state,mediaPaths),
                StandardCharsets.UTF_8)).getString("snapshot_id");
            if(!expected.equals(current))
                throw new IOException("Phone changed since the PC snapshot; export a fresh snapshot and reattach saved playlists");
            if(commitMutation("Import PC playlists",next->PhonePlaylistImport.apply(next,specs))){
                selectedPlaylist="";selectedTrack="";showHome();
                message("Imported "+specs.size()+" playlists. Invalid playback positions reset; bookmarks retained. " +
                        "No audio files were changed. Imported file retained for inspection.");
            }
        }catch(Exception error){
            message("Import refused: "+error.getClass().getSimpleName()+" — "+error.getMessage());
        }
    }
    @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] results){
        super.onRequestPermissionsResult(request,permissions,results);
        if(request==PERMISSION_REQUEST && results.length>0 && results[0]==PackageManager.PERMISSION_GRANTED)scanLibrary();
        else if(request==PERMISSION_REQUEST)message("Audio permission denied. Saved playlists are visible; playback is unavailable.");
    }
    private void resume(boolean book){
        PlayerState.Progress p=state.progress(book);
        if(p.playlistId.isEmpty()||p.trackKey.isEmpty()){message("No saved "+(book?"audiobook":"music")+" session");return;}
        PlayerState.Playlist pl=state.playlists.get(p.playlistId);
        if(pl==null || pl.audiobook!=book || !pl.entries.contains(p.trackKey)){
            message("Saved playlist/track no longer matches. No substitution was made.");return;
        }
        int idx=pl.entries.indexOf(p.trackKey);playFrom(pl,idx,true);
    }
    private void playFrom(PlayerState.Playlist p,int index,boolean resume){
        stopPreview();
        if(playback==null || !mediaReady){message("Audio service/library not ready");return;}
        if(index<0 || index>=p.entries.size())return;
        String key=p.entries.get(index);
        if(!state.tracks.containsKey(key)||missing.contains(key)||conflicts.contains(key)){
            message("Track missing or changed. No title-based substitution.");return;
        }
        // Explicit Play is the only entry point that starts the foreground service.
        startForegroundService(new Intent(this,KeypadPlaybackService.class));
        if(!playback.playFrom(p.id,index,resume)){
            message(playback.lastError());return;
        }
        state=playback.state;activeBook=playback.activeBook;showNow();
    }
    private void nowShortcut(int key){
        if(playback==null)return;
        switch(key){
            case KeyEvent.KEYCODE_1:seekBy(-10000);break;
            case KeyEvent.KEYCODE_3:seekBy(10000);break;
            case KeyEvent.KEYCODE_4:playback.skip(-1);showNow();break;
            case KeyEvent.KEYCODE_6:playback.skip(1);showNow();break;
            case KeyEvent.KEYCODE_5:
                if(!playback.isPrepared()){message("No prepared track");break;}
                if(!playback.isPlaying())startForegroundService(new Intent(this,KeypadPlaybackService.class));
                playback.toggle();showNow();break;
            case KeyEvent.KEYCODE_0:if(activeBook)saveQuickBookmark();break;
            case KeyEvent.KEYCODE_7:if(activeBook)jumpBookmark(-1);break;
            case KeyEvent.KEYCODE_9:if(activeBook)jumpBookmark(1);break;
            case KeyEvent.KEYCODE_POUND:if(activeBook)showBookmarks();break;
            default:break;
        }
    }
    private String titleForKey(String key){
        PlayerState.Track t=key==null?null:state.tracks.get(key);
        return t==null?"—":(t.title.isEmpty()?"(untitled)":t.title);
    }
    private static String shortTitle(String title){
        return title.length()>34?title.substring(0,33)+"…":title;
    }
    private String nowFooter(){
        if(playback==null || state==null)return "Playback unavailable";
        PlayerState.Progress p=state.progress(activeBook);
        PlayerState.Track t=state.tracks.get(p.trackKey);
        String duration=t==null || t.durationMs<=0?"unknown":clock(t.durationMs);
        return (playback.isPlaying()?"Playing ":"Paused ")+clock(playback.position())+" / "+duration+
            " · Sleep "+sleepTimerLabel()+"\n"+
            "1 -10s · 3 +10s · 4 Prev · 6 Next · 5 Play/Pause"+
            (activeBook?"\n0 Save mark · 7/9 Jump marks · # Browse marks":"");
    }
    private void showNow(){
        if(state==null)return;
        reset("NOW");PlayerState.Progress p=state.progress(activeBook);
        item("[5] Play / Pause",()->nowShortcut(KeyEvent.KEYCODE_5));
        item("[1] ◀ Back 10 seconds",()->seekBy(-10000));
        item("[3] Forward 10 seconds ▶",()->seekBy(10000));
        item("[4] Previous playlist track",()->{if(playback!=null){playback.skip(-1);showNow();}});
        item("[6] Next playlist track",()->{if(playback!=null){playback.skip(1);showNow();}});
        item("Shuffle: "+(playback!=null && playback.shuffleEnabled()?"ON":"OFF"),()->{
            if(playback!=null){playback.setShuffle(!playback.shuffleEnabled());showNow();}
        });
        item("Repeat: "+repeatLabel(),()->{
            if(playback!=null){playback.cycleRepeat();showNow();}
        });
        item("Sleep timer: "+sleepTimerLabel(),this::showSleepTimerOptions);
        if(activeBook){
            item("[0] Save bookmark now",this::saveQuickBookmark);
            item("[7] Previous bookmark",()->jumpBookmark(-1));
            item("[9] Next bookmark",()->jumpBookmark(1));
            item("[#] Browse / edit bookmarks",this::showBookmarks);
        }
        item("← Home (pauses)",()->{pauseForNavigation();showHome();});
        PlayerState.Playlist pl=state.playlists.get(p.playlistId);
        NowPlayingNavigation.Neighbors adjacent=pl==null?
            NowPlayingNavigation.neighbors(null,null,p.trackKey,false,false):
            NowPlayingNavigation.neighbors(pl.entries,
                playback==null?null:playback.playbackOrderSnapshot(),p.trackKey,
                playback!=null && playback.shuffleEnabled(),
                playback!=null && playback.repeatMode()==org.roarin.kyocerakeypad.core.PlaylistPlaybackOrder.Repeat.PLAYLIST);
        String orderHint=adjacent.sessionShuffleOrder?" (shuffle order)":"";
        render("Prev"+orderHint+": "+shortTitle(titleForKey(adjacent.previousKey))+"\n"+
            "▶ "+shortTitle(titleForKey(p.trackKey))+"\n"+
            "Next"+orderHint+": "+shortTitle(titleForKey(adjacent.nextKey)),nowFooter());
    }
    private void saveQuickBookmark(){
        if(!activeBook || playback==null || !playback.isPrepared()){
            message("Open an audiobook track first");return;
        }
        PlayerState.Progress p=state.progress(true);
        final String key=p.trackKey;
        final long at=currentPosition();
        if(key.isEmpty())return;
        if(commitMutation("Add bookmark",next->next.addBookmark(key,clock(at),at))){
            showNow();footer.setText("Saved bookmark "+clock(at)+"\n"+nowFooter());
        }
    }
    private void jumpBookmark(int direction){
        if(!activeBook || playback==null || !playback.isPrepared()){
            message("Open an audiobook track first");return;
        }
        PlayerState.Progress p=state.progress(true);
        int index=NowPlayingNavigation.bookmarkIndex(state.bookmarks,p.trackKey,currentPosition(),direction);
        if(index<0){message(direction<0?"No earlier bookmark on this track":"No later bookmark on this track");return;}
        playback.seekAbsolute(state.bookmarks.get(index).positionMs);showNow();
    }
    private long currentPosition(){
        return playback==null?0:playback.position();
    }
    private void seekBy(long delta){
        if(playback==null || !playback.isPrepared()){message("Track not prepared");return;}
        playback.seek(delta);showNow();
    }
    private void showBookmarks(){
        reset("BOOKMARKS");PlayerState.Progress p=state.progress(true);
        for(int i=0;i<state.bookmarks.size();i++){
            PlayerState.Bookmark b=state.bookmarks.get(i);if(!b.trackKey.equals(p.trackKey))continue;
            final int index=i;
            item(b.name+" — "+clock(b.positionMs),()->bookmarkActions(index));
        }
        item("← Playing",this::showNow);render("Audiobook bookmarks","Choose one to jump, rename or delete.");
    }
    private void bookmarkActions(int index){
        PlayerState.Bookmark b=state.bookmarks.get(index);reset("BOOKMARK_ACTIONS");
        item("Jump to bookmark",()->{
            if(playback!=null && playback.isPrepared()){
                playback.seekAbsolute(b.positionMs);showNow();}
            else message("Open audiobook first");
        });
        item("Rename bookmark",()->prompt("Bookmark name",b.name,name->{if(commitMutation("Rename bookmark",next->next.renameBookmark(index,name)))showBookmarks();}));
        item("Delete bookmark",()->new AlertDialog.Builder(this).setMessage("Delete this bookmark?")
            .setNegativeButton("Cancel",(d,w)->{}).setPositiveButton("Delete",(d,w)->{
                if(commitMutation("Delete bookmark",next->next.deleteBookmark(index)))showBookmarks();
            }).show());
        item("← Back",this::showBookmarks);render(b.name,"Bookmark changes do not change the audio file.");
    }
    private void saveActivePosition(){if(playback!=null)playback.savePosition();}
    private boolean stopPlayer(){return playback!=null && playback.stopPlayer();}
    /** Edits a decoded copy, writes it durably, then publishes one shared state. */
    private boolean commitMutation(String label,java.util.function.Consumer<PlayerState> edit){
        if(recoveryMode || playback==null){message(label+" blocked: playback state unavailable.");return false;}
        try{
            PlayerState next=StateMutation.prepareAndSave(state,edit,this::writeStateBytes);
            if(next==state){message(label+" not saved; previous data retained.");return false;}
            playback.state=next;state=next;return true;
        }catch(Exception e){message(label+" not applied: "+e.getClass().getSimpleName());return false;}
    }
    private boolean writeStateBytes(byte[] data){return playback!=null && playback.writeStateBytes(data);}
    private boolean persist(){
        if(playback!=null && playback.persist())return true;
        message("Could not save player state; preserve app data.");return false;
    }
    private void pauseForNavigation(){if(playback!=null)playback.pause();}
    private static AudioAttributes mediaAttributes(boolean book){
        return new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA)
            .setContentType(book?AudioAttributes.CONTENT_TYPE_SPEECH:AudioAttributes.CONTENT_TYPE_MUSIC).build();
    }
    private boolean requestAudioFocusForExplicitPlay(boolean book){
        return playback!=null && playback.requestFocus(book);
    }
    private void abandonAudioFocus(){if(playback!=null)playback.abandonFocus();}
    @Override public void onResume(){super.onResume();}
    // Screen sleep, flip close and app switching MUST NOT imply explicit Home pause.
    @Override public void onPause(){stopPreview();super.onPause();}
    @Override public void onDestroy(){
        timer.removeCallbacks(tick);stopPreview();
        if(playback!=null)playback.setListener(null);
        if(bound){unbindService(serviceConnection);bound=false;}
        super.onDestroy();
    }
    @Override public void onBackPressed(){
        switch(screen){
            case "HOME":super.onBackPressed();break;
            case "HOME_REORDER":finishHomeReorder(false);break;
            case "PLAYLISTS":case "HELP":case "SETTINGS":showHome();break;
            case "ALPHABET":restoreLibrary();break;
            case "LIBRARY_TRACK":returnToLibrary();break;
            case "LIBRARY_ADD":showLibraryTrackActions(libraryTrackKey);break;
            case "PREVIEW":returnFromPreview();break;
            case "NOW":pauseForNavigation();showHome();break;
            case "DETAIL":showPlaylists(browsingBook);break;
            case "MOVE":cancelMoveMode();break;
            case "TRACK_ACTIONS":case "LIBRARY":if(adding){adding=false;showDetail();}else if("TRACK_ACTIONS".equals(screen))showDetail();else showHome();break;
            case "BOOKMARK_ACTIONS":showBookmarks();break;
            case "BOOKMARKS":showNow();break;
            default:showHome();
        }
    }
}
