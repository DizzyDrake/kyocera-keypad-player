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
import org.roarin.kyocerakeypad.core.AlphabetJump;
import org.roarin.kyocerakeypad.core.StateMutation;
import org.roarin.kyocerakeypad.core.FailedOpenRollback;
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
            playback=null;state=null;actions.clear();labels.clear();
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
    private ListView list;
    private final ArrayList<Runnable> actions=new ArrayList<>();
    private final ArrayList<String> labels=new ArrayList<>();
    private final ArrayList<String> visibleLibraryTitles=new ArrayList<>();
    private int libraryReturnSelection=0;
    private long lastPersistAt=0L;

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
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
        if(playback!=null && playback.isPlaying() && "NOW".equals(screen))
            footer.setText("Playing: "+clock(playback.position())+"  |  Center selects action");
        timer.postDelayed(this,2000);
    }};
    private static String clock(long ms){long s=Math.max(0,ms)/1000;return String.format(Locale.US,"%02d:%02d:%02d",s/3600,(s/60)%60,s%60);}
    private void render(String title,String hint){
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
    private void showHome(){
        reset("HOME");
        item("Music playlists",()->showPlaylists(false));
        item("Audiobook playlists",()->showPlaylists(true));
        item("Browse / search local audio",()->showLibrary(false));
        item("Resume music (explicit play)",()->resume(false));
        item("Resume audiobook (explicit play)",()->resume(true));
        item("Export metadata for PC (manual)",this::confirmMetadataExport);
        item("Help / controls",this::showHelp);
        item("About / version",this::showAbout);
        render("WQB405 · UNBUILT PROTOTYPE",mediaReady?"D-pad moves · Center selects · Back returns":"Audio permission needed for library playback");
    }
    private void showAbout(){
        // BUILD_UTC is generated by Gradle configuration on the builder's machine.
        // No build timestamp is invented for an uncompiled source-only ZIP.
        message("Keypad Player · DISPOSABLE SANDBOX\nApplication ID: "+getPackageName()+"\nVersion: "+BuildConfig.VERSION_NAME+
            "\nBuild configured UTC: "+BuildConfig.BUILD_UTC+
            "\nSource prototype prepared: 2026-10-28"+
            "\nRelease date: Not released"+
            "\nUNBUILT prototype. Distinct from original and WQA365 sandbox."+
            "\nMade by GPT-6 and Aurora Williamsen"+
            "\nOffline player · No cloud upload");
    }
    private void showHelp(){
        reset("HELP");item("Back to home",this::showHome);
        item("Playlists: select an item to reorder or remove",()->message("Use Move up / Move down in track actions. Order is never alphabetized."));
        item("Now playing: seek 10 seconds or bookmark",()->message("Music and audiobook progress are separate. No autoplay on launch."));
        item("About / version",this::showAbout);
        item("Safety / limitations",()->message("EXISTING SANDBOX UPDATE. This build uses the same app-private playlists and progress as the previous WQA365 sandbox when updated in place; it stays separate from the original player. Use disposable test media. No cloud. Do not uninstall either app to resolve signing problems. MediaStore IDs can change; missing/changed files are blocked."));
        render("Help","D-pad Up/Down · Center selects · Back returns. Physical E4831 validation pending.");
    }
    private void showPlaylists(boolean book){
        browsingBook=book;reset("PLAYLISTS");
        item("+ Create playlist",()->prompt("Playlist name","",name->{
            String id=UUID.randomUUID().toString();
            if(commitMutation("Create playlist",next->next.createPlaylist(id,name,book))){
                selectedPlaylist=id;showDetail();
            }
        }));
        for(PlayerState.Playlist p:state.playlists.values())if(p.audiobook==book){
            item(p.name+" ("+p.entries.size()+" tracks)",()->{selectedPlaylist=p.id;showDetail();});
        }
        item("← Back",this::showHome);
        render(book?"Audiobook playlists":"Music playlists","Create, reorder and play on phone; no PC needed for these operations.");
    }
    private void showDetail(){
        PlayerState.Playlist p=state.playlists.get(selectedPlaylist);
        if(p==null){showPlaylists(browsingBook);return;}
        browsingBook=p.audiobook;reset("DETAIL");
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
        int i=0;
        for(String key:p.entries){final int idx=i++;PlayerState.Track t=state.tracks.get(key);
            String title=t==null?"[missing identity]":t.title;
            item(i+". "+title+((missing.contains(key)||conflicts.contains(key))?" [unavailable]":""),()->{
                selectedTrack=key;showTrackActions(idx);
            });
        }
        item("← Playlists",()->showPlaylists(p.audiobook));
        render(p.name,"Order shown is playback order. Select a track for Play, Move, Remove.");
    }
    private void showTrackActions(int index){
        PlayerState.Playlist p=state.getPlaylist(selectedPlaylist);
        if(index<0 || index>=p.entries.size()){showDetail();return;}
        String key=p.entries.get(index);PlayerState.Track t=state.tracks.get(key);
        reset("TRACK_ACTIONS");
        item("Play this track",()->playFrom(p,index,false));
        item("Move up",()->{if(index>0)commitMutation("Move track up",next->next.move(p.id,index,index-1));
            showDetail();});
        item("Move down",()->{if(index<p.entries.size()-1)commitMutation("Move track down",next->next.move(p.id,index,index+1));
            showDetail();});
        item("Remove from playlist (audio kept)",()->{commitMutation("Remove track",next->next.remove(p.id,index));showDetail();});
        item("← Back",this::showDetail);
        render(t==null?"Missing track":t.title,"Select action. Reordering never changes the audio file.");
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
            .setMessage("Creates a local JSON snapshot of track names/paths, playlists, bookmarks and positions in this app's transfer folder. No audio copied. Filenames can be private. Use ADB only if you choose to later. No import available yet.")
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
            message("Exported metadata only ("+json.length+" bytes) to: "+dest.getAbsolutePath()+"\nADB pull is owner-invoked. No phone import or automatic sync.");
        } catch(Exception error) {
            message("Export refused/failed: "+error.getClass().getSimpleName()+" — "+error.getMessage());
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
    private void showNow(){
        reset("NOW");PlayerState.Progress p=state.progress(activeBook);
        item("Play / Pause",()->{
            if(playback==null || !playback.isPrepared()){message("No prepared track");return;}
            if(!playback.isPlaying())startForegroundService(new Intent(this,KeypadPlaybackService.class));
            playback.toggle();showNow();
        });
        item("◀ Back 10 seconds",()->seekBy(-10000));
        item("Forward 10 seconds ▶",()->seekBy(10000));
        if(activeBook){item("+ Save timestamp bookmark",()->prompt("Bookmark name",clock(currentPosition()),name->{
            long at=currentPosition();
            if(commitMutation("Add bookmark",next->next.addBookmark(p.trackKey,name,at)))showNow();
        }));item("Browse / edit bookmarks",this::showBookmarks);}
        item("← Home (pauses)",()->{pauseForNavigation();showHome();});
        PlayerState.Track t=state.tracks.get(p.trackKey);
        render(t==null?"Now playing":t.title,"No autoplay on relaunch. D-pad Center activates actions.");
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
            case "PLAYLISTS":case "HELP":showHome();break;
            case "ALPHABET":restoreLibrary();break;
            case "LIBRARY_TRACK":returnToLibrary();break;
            case "LIBRARY_ADD":showLibraryTrackActions(libraryTrackKey);break;
            case "PREVIEW":returnFromPreview();break;
            case "NOW":pauseForNavigation();showHome();break;
            case "DETAIL":showPlaylists(browsingBook);break;
            case "TRACK_ACTIONS":case "LIBRARY":if(adding){adding=false;showDetail();}else if("TRACK_ACTIONS".equals(screen))showDetail();else showHome();break;
            case "BOOKMARK_ACTIONS":showBookmarks();break;
            case "BOOKMARKS":showNow();break;
            default:showHome();
        }
    }
}
