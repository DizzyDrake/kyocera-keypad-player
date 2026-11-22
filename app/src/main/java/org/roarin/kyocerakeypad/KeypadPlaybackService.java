package org.roarin.kyocerakeypad;

import android.app.*;
import android.content.*;
import android.media.*;
import android.media.session.MediaSession;
import android.media.session.PlaybackState;
import android.net.Uri;
import android.os.*;
import android.view.KeyEvent;
import java.util.List;
import java.util.Random;
import android.util.AtomicFile;
import org.roarin.kyocerakeypad.core.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

/**
 * WQB405 OFFLINE INTEGRATION PROTOTYPE — NOT SDK-COMPILED OR DEVICE-ACCEPTED.
 * Owns the single PlayerState/AtomicFile and MediaPlayer, rather than letting
 * Activity.onPause/onDestroy terminate intentional background listening.
 * All binder and media callbacks run on Android's main looper. No autoplay on
 * process recreation, focus gain, app launch, headset connection or bind.
 */
public final class KeypadPlaybackService extends Service {
    static final String CHANNEL = "keypad_playback_wqb405";
    static final int NOTIFICATION_ID = 405;
    static final String ACTION_TOGGLE = "org.roarin.kyocerakeypad.WQB405_TOGGLE";
    static final String ACTION_NEXT = "org.roarin.kyocerakeypad.WQB405_NEXT";
    static final String ACTION_PREVIOUS = "org.roarin.kyocerakeypad.WQB405_PREVIOUS";
    private final MediaTransportSequencer transport=new MediaTransportSequencer(350);
    // Experimental double-NEXT is opt-in. A volume-down tap is NOT remapped.
    private final Runnable mediaFlush = () -> {
        for (MediaTransportSequencer.Action action : transport.flush(SystemClock.elapsedRealtime()))
            performMediaAction(action);
    };
    private final PlaylistPlaybackOrder playbackOrder = new PlaylistPlaybackOrder();
    private final Random shuffleRandom = new Random();
    private boolean shuffleMusic, shuffleBook, experimentalDoubleNext;
    // Independent remote media Next/Previous seek preferences: audiobook ON, music OFF.
    private boolean remoteSeekBook=true, remoteSeekMusic=false;
    private PlaylistPlaybackOrder.Repeat repeatMode = PlaylistPlaybackOrder.Repeat.OFF;
    final IBinder binder = new LocalBinder();
    final Handler handler = new Handler(Looper.getMainLooper());
    // Retired in ordinary builds: volume-index polling cannot detect presses at max/min.
    // Diagnostic builds retain it for controlled experiments only.
    // Observes system volume indices so the existing Android volume routing
    // and MediaSession media-button handler remain unchanged. This can also
    // react to local/device volume changes; it cannot identify the headset.
    private final VolumeDoubleTapSeek volumeDoubleTap=new VolumeDoubleTapSeek(650L);
    private boolean volumeDoubleSeekEnabled;
    private final Runnable volumeDoubleSeekPoll=new Runnable(){@Override public void run(){
        if(!volumeDoubleSeekEnabled)return;
        boolean playing=isPlaying();
        long delayMs=playing?100L:500L;
        if(audioManager!=null){
            try{
                int current=audioManager.getStreamVolume(AudioManager.STREAM_MUSIC);
                if(playing && !btProbeActive){
                    VolumeDoubleTapSeek.Action action=volumeDoubleTap.observe(current,SystemClock.elapsedRealtime());
                    if(action==VolumeDoubleTapSeek.Action.FORWARD_30S)seek(30000L);
                    else if(action==VolumeDoubleTapSeek.Action.BACK_15S)seek(-15000L);
                }else volumeDoubleTap.reset(current);
            }catch(RuntimeException ignored){volumeDoubleTap.clear();}
        }else volumeDoubleTap.clear();
        if(volumeDoubleSeekEnabled)handler.postDelayed(this,delayMs);
    }};
    boolean isVolumeDoubleSeekEnabled(){return volumeDoubleSeekEnabled;}
    void setVolumeDoubleSeekEnabled(boolean enabled){
        // No amount of timing adjustment makes saturated volume indexes observable.
        if(!BuildConfig.DEBUG) enabled=false;
        volumeDoubleSeekEnabled=enabled;
        handler.removeCallbacks(volumeDoubleSeekPoll);
        volumeDoubleTap.clear();
        if(enabled)handler.post(volumeDoubleSeekPoll);
        getSharedPreferences("playlist_playback_options_v1",MODE_PRIVATE).edit()
            .putBoolean("double_volume_seek",enabled).apply();
    }
    // Experimental 45-second, user-initiated read-only Bluetooth diagnostic.
    // Does not intercept volume or alter media commands. No background collection.
    private static final long BT_PROBE_LENGTH_MS=45000L;
    private static final long BT_PROBE_SAMPLE_MS=100L;
    private boolean btProbeActive;
    private long btProbeStarted;
    private int btProbeLastVolume;
    private StringBuilder btProbeNotes;
    private String btProbeLastFile="";
    private final Runnable btProbeSample=new Runnable(){@Override public void run(){
        if(!btProbeActive)return;
        long elapsed=SystemClock.elapsedRealtime()-btProbeStarted;
        if(elapsed>=BT_PROBE_LENGTH_MS){finishBluetoothDiagnostic("45-second recording finished");return;}
        if(audioManager!=null){
            try{
                int current=audioManager.getStreamVolume(AudioManager.STREAM_MUSIC);
                if(current!=btProbeLastVolume){
                    btProbeNote("music_stream_volume " + btProbeLastVolume + " -> " + current);
                    btProbeLastVolume=current;
                }
            }catch(RuntimeException e){btProbeNote("music_volume_read_error " + e.getClass().getSimpleName());}
        }
        handler.postDelayed(this,BT_PROBE_SAMPLE_MS);
    }};
    // Start while Dumbplayer is playing; the service remains running with the flip closed.
    // The diagnostic records timing, media key codes, callbacks, and music volume INDEX only.
    // It never records song titles, filenames, phone identifiers or Bluetooth addresses.
    boolean startBluetoothDiagnostic(){
        if(btProbeActive || audioManager==null)return false;
        btProbeActive=true;
        btProbeStarted=SystemClock.elapsedRealtime();
        btProbeNotes=new StringBuilder(2048);
        try{btProbeLastVolume=audioManager.getStreamVolume(AudioManager.STREAM_MUSIC);}
        catch(RuntimeException e){btProbeLastVolume=-1;}
        btProbeNote("START music_stream_volume="+btProbeLastVolume+" max="+
            audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC));
        btProbeNote("ACTION: tap Volume Up once, double Up, tap Down once, double Down, optionally hold Next");
        btProbeNote("LIMIT: Android may not deliver volume keys to a MediaSession; absence is inconclusive");
        handler.post(btProbeSample);
        return true;
    }
    private void btProbeNote(String event){
        if(!btProbeActive || btProbeNotes==null)return;
        if(btProbeNotes.length()>32000)return; // bounded, even if a noisy headset repeats
        btProbeNotes.append(SystemClock.elapsedRealtime()-btProbeStarted)
            .append("ms  ").append(event).append('\n');
    }
    private void finishBluetoothDiagnostic(String reason){
        if(!btProbeActive)return;
        btProbeNote("END " + reason);
        btProbeActive=false;
        handler.removeCallbacks(btProbeSample);
        try{
            File dir=getExternalFilesDir("transfer");
            if(dir==null || (!dir.isDirectory() && !dir.mkdirs()))throw new IOException("Transfer directory unavailable");
            File dest=new File(dir,"bt_probe_"+System.currentTimeMillis()+".txt");
            AtomicFile output=new AtomicFile(dest);
            FileOutputStream out=null;
            try{
                out=output.startWrite();
                out.write(btProbeNotes.toString().getBytes(StandardCharsets.UTF_8));
                output.finishWrite(out);
            }catch(Exception e){if(out!=null)output.failWrite(out);throw e;}
            btProbeLastFile=dest.getAbsolutePath();
        }catch(Exception e){
            btProbeLastFile="SAVE FAILED: "+e.getClass().getSimpleName();
            android.util.Log.w("DumbplayerBtProbe",btProbeLastFile);
        }finally{btProbeNotes=null;}
    }
    String latestBluetoothDiagnosticPath(){return btProbeLastFile;}
    PlayerState state = new PlayerState();
    boolean recoveryMode, activeBook, prepared;
    MediaPlayer player;
    private AtomicFile store;
    private AudioManager audioManager;
    private AudioFocusRequest focusRequest;
    private final PlaybackGate playbackGate = new PlaybackGate();
    private final AudioFocusGate focusGate = new AudioFocusGate();
    private long focusEpoch;
    // DEV17: one-shot permission to resume a session temporarily paused by a
    // notification/focus loss, never by manual Pause, Stop, or permanent loss.
    private boolean transientResumePending;
    // Do not start while seekTo(audiobook resume offset) is still pending.
    private boolean awaitingInitialSeek;
    private long trackTransitionCount;
    private void playbackEvent(String event){
        // Bounded identifier-free diagnosis for closed-flip shuffle delays.
        android.util.Log.d("DumbplayerPlayback", "transition="+trackTransitionCount+
            " elapsedMs="+SystemClock.elapsedRealtime()+" "+event);
    }
    private MediaSession mediaSession;
    private boolean foreground;
    private String lastError = "";
    private Listener listener;
    private long lastSaveAt;
    // Timer uses elapsedRealtime (includes screen-off sleep), never wall-clock changes.
    // It is deliberately NOT restored after process death: no stale timer or autoplay.
    private long sleepDeadlineElapsed = -1L;
    private String sleepPlaylistId = "";
    private boolean sleepBook;
    private int audiobookRewindSeconds;
    private final Runnable sleepTimerExpiry = new Runnable() { @Override public void run() {
        if (sleepDeadlineElapsed < 0L) return;
        long remaining=SleepTimerPolicy.remainingMs(SystemClock.elapsedRealtime(),sleepDeadlineElapsed);
        if (remaining > 0L) { handler.postDelayed(this,remaining);return; }
        PlayerState.Progress p=state.progress(activeBook);
        boolean sameSession=(activeBook==sleepBook && sleepPlaylistId.equals(p.playlistId));
        clearSleepTimer();
        if (sameSession) pause(); // Durably save playhead; never restart audio.
        else notifyChanged(); // A changed session must not inherit an old timer.
    }};

    public final class LocalBinder extends Binder {
        public KeypadPlaybackService service() { return KeypadPlaybackService.this; }
    }
    interface Listener { void onPlaybackChanged(); void onPlaybackError(String error); }
    void setListener(Listener next) { listener = next; }
    String lastError() { return lastError; }
    @Override public IBinder onBind(Intent intent) { return binder; }

    @Override public void onCreate() {
        super.onCreate();
        store = new AtomicFile(new File(getFilesDir(), "keypad_player_state_v1.bin"));
        File f = new File(getFilesDir(), "keypad_player_state_v1.bin");
        if (f.exists() || new File(f.getPath()+".bak").exists()) {
            try (InputStream in=store.openRead()) {
                ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                byte[] b=new byte[8192]; int n;
                while ((n=in.read(b))!=-1) {
                    if (bytes.size()+n>16*1024*1024) throw new IOException("Oversize state");
                    bytes.write(b,0,n);
                }
                state=StateCodec.decode(bytes.toByteArray());
            } catch (Exception e) { recoveryMode=true; }
        }
        android.content.SharedPreferences settings=getSharedPreferences("playlist_playback_options_v1",MODE_PRIVATE);
        // Legacy single preference is inherited by each lane on first upgrade.
        // Later toggles are independent and never rewrite the other lane.
        boolean legacyShuffle=settings.getBoolean("shuffle",false);
        shuffleMusic=settings.getBoolean("shuffle_music",legacyShuffle);
        shuffleBook=settings.getBoolean("shuffle_book",legacyShuffle);
        remoteSeekBook=settings.getBoolean("remote_seek_book",true);
        remoteSeekMusic=settings.getBoolean("remote_seek_music",false);
        String savedRepeat=settings.getString("repeat","OFF");
        try { repeatMode=PlaylistPlaybackOrder.Repeat.valueOf(savedRepeat); }
        catch (IllegalArgumentException ignored) { repeatMode=PlaylistPlaybackOrder.Repeat.OFF; }
        experimentalDoubleNext=BuildConfig.DEBUG && settings.getBoolean("double_next_seek",false);
        volumeDoubleSeekEnabled=BuildConfig.DEBUG && settings.getBoolean("double_volume_seek",false);
        audiobookRewindSeconds=settings.getInt("audiobook_resume_rewind_seconds",0);
        if(audiobookRewindSeconds!=0 && audiobookRewindSeconds!=5 && audiobookRewindSeconds!=10)
            audiobookRewindSeconds=0;
        transport.setDoubleSeekEnabled(experimentalDoubleNext);
        audioManager=(AudioManager)getSystemService(Context.AUDIO_SERVICE);
        playbackGate.onResume(); // Service lifecycle is independent of screen visibility.
        NotificationChannel channel=new NotificationChannel(CHANNEL,"Keypad playback",NotificationManager.IMPORTANCE_LOW);
        ((NotificationManager)getSystemService(Context.NOTIFICATION_SERVICE)).createNotificationChannel(channel);
        mediaSession=new MediaSession(this,"KeypadPlaybackWQB405");
        mediaSession.setFlags(MediaSession.FLAG_HANDLES_MEDIA_BUTTONS|MediaSession.FLAG_HANDLES_TRANSPORT_CONTROLS);
        mediaSession.setCallback(new MediaSession.Callback(){
            @Override public void onPlay(){ btProbeNote("MediaSession.onPlay"); explicitPlay(); }
            @Override public void onPause(){ btProbeNote("MediaSession.onPause"); pause(); }
            @Override public void onStop(){ btProbeNote("MediaSession.onStop"); stopPlayer(); }
            @Override public void onSkipToNext(){ btProbeNote("MediaSession.onSkipToNext"); remoteNextPrevious(true); }
            @Override public void onSkipToPrevious(){ btProbeNote("MediaSession.onSkipToPrevious"); remoteNextPrevious(false); }
            @Override public void onSeekTo(long pos){ btProbeNote("MediaSession.onSeekTo"); seekAbsolute(pos); }
            @Override public boolean onMediaButtonEvent(Intent eventIntent){
                KeyEvent key=eventIntent==null?null:eventIntent.getParcelableExtra(Intent.EXTRA_KEY_EVENT);
                if(key==null){btProbeNote("MediaSession.onMediaButtonEvent: missing KeyEvent");return false;}
                btProbeNote("MediaSession.onMediaButtonEvent key="+KeyEvent.keyCodeToString(key.getKeyCode())+
                    " action="+key.getAction()+" repeat="+key.getRepeatCount());
                if(key.getAction()==KeyEvent.ACTION_DOWN && key.getRepeatCount()==0){
                    MediaTransportSequencer.Key mapped=mapMediaKey(key.getKeyCode());
                    if(mapped==MediaTransportSequencer.Key.UNKNOWN)return false;
                    for(MediaTransportSequencer.Action action:transport.onPress(mapped,SystemClock.elapsedRealtime()))
                        performMediaAction(action);
                    handler.removeCallbacks(mediaFlush);
                    if (transport.hasPending()) {
                        long delay=Math.max(1,transport.pendingDeadlineMs()-SystemClock.elapsedRealtime());
                        handler.postDelayed(mediaFlush,delay);
                    }
                }
                return true; // Consume corresponding UP/repeats, avoid duplicate dispatch.
            }
        },handler);
        mediaSession.setActive(true);
        updateMediaSession();
        handler.postDelayed(saveTick,5000);
        if(volumeDoubleSeekEnabled)handler.post(volumeDoubleSeekPoll);
    }
    @Override public int onStartCommand(Intent intent,int flags,int startId) {
        // A foreground-service start is issued only on explicit Play/Resume.
        // Start foreground promptly even while MediaPlayer prepares asynchronously.
        if (!recoveryMode){
            showForeground();
            String action=intent==null?null:intent.getAction();
            if(ACTION_TOGGLE.equals(action))toggle();
            else if(ACTION_NEXT.equals(action))remoteNextPrevious(true);
            else if(ACTION_PREVIOUS.equals(action))remoteNextPrevious(false);
            // A pending start may arrive after Play failed or was paused. Honor
            // the foreground deadline first, then retire the idle start.
            if (player == null) retireForeground();
            else if (isPrepared() && !isPlaying() && !transientResumePending) keepPausedControls();
        } else { showForegroundForRecovery(); stopSelf(startId); }
        return START_NOT_STICKY; // Never automatically resume after process death.
    }
    private static MediaTransportSequencer.Key mapMediaKey(int code){
        switch(code){
            case KeyEvent.KEYCODE_MEDIA_PLAY: return MediaTransportSequencer.Key.PLAY;
            case KeyEvent.KEYCODE_MEDIA_PAUSE: return MediaTransportSequencer.Key.PAUSE;
            case KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE:
            case KeyEvent.KEYCODE_HEADSETHOOK: return MediaTransportSequencer.Key.PLAY_PAUSE;
            case KeyEvent.KEYCODE_MEDIA_NEXT: return MediaTransportSequencer.Key.NEXT;
            case KeyEvent.KEYCODE_MEDIA_PREVIOUS: return MediaTransportSequencer.Key.PREVIOUS;
            case KeyEvent.KEYCODE_MEDIA_STOP: return MediaTransportSequencer.Key.STOP;
            default: return MediaTransportSequencer.Key.UNKNOWN;
        }
    }
    private void performMediaAction(MediaTransportSequencer.Action action){
        switch(action){
            case PLAY: explicitPlay();break;
            case PAUSE: pause();break;
            case TOGGLE: toggle();break;
            case NEXT: remoteNextPrevious(true);break;
            case PREVIOUS: remoteNextPrevious(false);break;
            case STOP: stopPlayer();break;
            case SEEK_FORWARD_10S: seek(10000);break;
            case SEEK_BACK_10S: seek(-10000);break;
        }
    }
    /**
     * Remote headset/media-session/notification NEXT/PREVIOUS (not the local
     * keypad [4]/[6] controls). Only current active lane determines behavior.
     * Absent a prepared track, seek mode is a no-op rather than silently
     * changing to another audiobook. Normal track commands still call skip().
     */
    private void remoteNextPrevious(boolean next){
        RemoteSkipPolicy.Action decision=RemoteSkipPolicy.decide(activeBook,remoteSeekMusic,remoteSeekBook,next);
        switch(decision){
            case SEEK_FORWARD_30S: seek(30000L);break;
            case SEEK_BACK_15S: seek(-15000L);break;
            case NEXT_TRACK: skip(1);break;
            case PREVIOUS_TRACK: skip(-1);break;
        }
    }
    boolean remoteSeekEnabled(boolean book){return book?remoteSeekBook:remoteSeekMusic;}
    void setRemoteSeek(boolean book,boolean enabled){
        if(book)remoteSeekBook=enabled;else remoteSeekMusic=enabled;
        getSharedPreferences("playlist_playback_options_v1",MODE_PRIVATE).edit()
            .putBoolean(book?"remote_seek_book":"remote_seek_music",enabled).apply();
        updateMediaSession();notifyChanged();
    }
    private final Runnable saveTick=new Runnable(){@Override public void run(){
        if(player!=null && prepared){
            try{if(player.isPlaying()){
                savePosition();
                if(SystemClock.elapsedRealtime()-lastSaveAt>=5000){
                    if(!persist()){pause();error("Position could not be saved; playback paused");}
                    lastSaveAt=SystemClock.elapsedRealtime();
                }
                updateMediaSession();notifyChanged();
            }}catch(IllegalStateException ignored){}
        }
        handler.postDelayed(this,5000);
    }};
    private static AudioAttributes attrs(boolean book){
        return new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA)
            .setContentType(book?AudioAttributes.CONTENT_TYPE_SPEECH:AudioAttributes.CONTENT_TYPE_MUSIC).build();
    }
    boolean writeStateBytes(byte[] data){
        if(recoveryMode)return false;
        FileOutputStream out=null;
        try{out=store.startWrite();out.write(data);store.finishWrite(out);return true;}
        catch(Exception e){if(out!=null)try{store.failWrite(out);}catch(Exception ignored){}return false;}
    }
    boolean persist(){
        if(recoveryMode)return false;
        try{return writeStateBytes(StateCodec.encode(state));}catch(Exception ignored){return false;}
    }
    void savePosition(){
        if(player!=null && prepared){try{state.savePosition(activeBook,player.getCurrentPosition());}catch(Exception ignored){}}
    }
    long position(){
        if(player!=null && prepared){try{return player.getCurrentPosition();}catch(Exception ignored){}}
        return state.progress(activeBook).positionMs;
    }
    boolean isPlaying(){try{return player!=null && prepared && player.isPlaying();}catch(Exception e){return false;}}
    boolean isPrepared(){return player!=null && prepared;}
    boolean stopPlayer(){
        transientResumePending=false;
        playbackGate.requestPause();savePosition();boolean saved=persist();abandonFocus();
        MediaPlayer old=player;player=null;prepared=false;awaitingInitialSeek=false;
        if(old!=null){try{old.reset();}catch(Exception ignored){}finally{try{old.release();}catch(Exception ignored){}}}
        retireForeground();updateMediaSession();notifyChanged();return saved;
    }
    void pause(){
        // Explicit owner action also cancels any transient auto-resume eligibility.
        transientResumePending=false;
        playbackGate.requestPause();
        if(isPlaying())try{player.pause();}catch(Exception failure){
            stopPlayer();error("Playback could not pause; player released");return;
        }
        savePosition();if (!persist()) error("Position could not be saved");
        abandonFocus();keepPausedControls();updateMediaSession();notifyChanged();
    }
    void explicitPlay(){
        transientResumePending=false;
        if(!isPrepared())return; // Never start from stale saved progress alone.
        if(requestFocus(activeBook)){
            playbackGate.requestPlay();
            try {
                if (!canStart()) { keepPausedControls(); return; }
                player.start();
                startForegroundService(new Intent(this, KeypadPlaybackService.class));
                showForeground();
            } catch(Exception e) {
                // Starting audio may have succeeded before the service start failed.
                // Release it so a reported failure cannot leave unowned audio running.
                stopPlayer();error("Playback could not resume");
            }
        }else {error("Audio unavailable during interruption; remains paused");keepPausedControls();}
        updateMediaSession();notifyChanged();
    }
    void toggle(){if(isPlaying())pause();else explicitPlay();}
    // Snapshot for display only. Playback order is service-owned and not re-shuffled by UI renders.
    List<String> playbackOrderSnapshot(){return playbackOrder.snapshot();}
    boolean shuffleEnabled(){return shuffleEnabled(activeBook);}
    boolean shuffleEnabled(boolean book){return book?shuffleBook:shuffleMusic;}
    PlaylistPlaybackOrder.Repeat repeatMode(){return repeatMode;}
    boolean experimentalDoubleNext(){return experimentalDoubleNext;}
    int audiobookRewindSeconds(){return audiobookRewindSeconds;}
    void cycleAudiobookRewind(){
        audiobookRewindSeconds=audiobookRewindSeconds==0?5:(audiobookRewindSeconds==5?10:0);
        getSharedPreferences("playlist_playback_options_v1",MODE_PRIVATE).edit()
            .putInt("audiobook_resume_rewind_seconds",audiobookRewindSeconds).apply();
        notifyChanged();
    }
    long sleepTimerRemainingMs(){
        return sleepDeadlineElapsed<0L?0L:SleepTimerPolicy.remainingMs(SystemClock.elapsedRealtime(),sleepDeadlineElapsed);
    }
    boolean sleepTimerArmed(){return sleepDeadlineElapsed>=0L;}
    boolean setSleepTimerMinutes(String minutes){
        if(!isPrepared()){error("Start a track before setting the sleep timer");return false;}
        final long duration;
        try{duration=SleepTimerPolicy.durationMs(minutes);}catch(IllegalArgumentException e){error(e.getMessage());return false;}
        long now=SystemClock.elapsedRealtime();
        if(duration>Long.MAX_VALUE-now){error("Timer duration too large");return false;}
        clearSleepTimer();
        PlayerState.Progress p=state.progress(activeBook);
        sleepPlaylistId=p.playlistId;sleepBook=activeBook;
        sleepDeadlineElapsed=now+duration;
        handler.postDelayed(sleepTimerExpiry,duration);
        notifyChanged();return true;
    }
    void cancelSleepTimer(){clearSleepTimer();notifyChanged();}
    private void clearSleepTimer(){
        handler.removeCallbacks(sleepTimerExpiry);
        sleepDeadlineElapsed=-1L;sleepPlaylistId="";
    }
    void setShuffle(boolean book,boolean enabled){
        if(book)shuffleBook=enabled;else shuffleMusic=enabled;
        getSharedPreferences("playlist_playback_options_v1",MODE_PRIVATE).edit()
            .putBoolean(book?"shuffle_book":"shuffle_music",enabled).apply();
        // Do not reshape a different active listening lane.
        if(activeBook==book){
            PlayerState.Progress progress=state.progress(activeBook);
            PlayerState.Playlist p=state.playlists.get(progress.playlistId);
            if(p!=null && p.entries.contains(progress.trackKey))
                playbackOrder.start(p.id,p.entries,progress.trackKey,enabled,shuffleRandom);
        }
        notifyChanged();
    }
    /**
     * WQB430: refresh non-shuffled session navigation after a durable playlist
     * reorder. Do not restart audio, change the current track or seek position.
     * With shuffle ON, the current shuffled session order intentionally remains.
     * If changing this, check PlaylistPlaybackOrder.matches/next and Move Mode.
     */
    void onPlaylistOrderSaved(String playlistId){
        PlayerState.Progress progress=state.progress(activeBook);
        PlayerState.Playlist p=state.playlists.get(playlistId);
        if(!shuffleEnabled(activeBook) && p!=null && playlistId.equals(progress.playlistId) &&
                p.entries.contains(progress.trackKey))
            playbackOrder.start(p.id,p.entries,progress.trackKey,false,shuffleRandom);
        notifyChanged();
    }
    void cycleRepeat(){
        switch(repeatMode){
            case OFF:repeatMode=PlaylistPlaybackOrder.Repeat.PLAYLIST;break;
            case PLAYLIST:repeatMode=PlaylistPlaybackOrder.Repeat.TRACK;break;
            default:repeatMode=PlaylistPlaybackOrder.Repeat.OFF;
        }
        getSharedPreferences("playlist_playback_options_v1",MODE_PRIVATE).edit()
            .putString("repeat",repeatMode.name()).apply();
        notifyChanged();
    }
    void setExperimentalDoubleNext(boolean enabled){
        handler.removeCallbacks(mediaFlush);
        for(MediaTransportSequencer.Action action:transport.setDoubleSeekEnabled(enabled))
            performMediaAction(action);
        experimentalDoubleNext=enabled;
        getSharedPreferences("playlist_playback_options_v1",MODE_PRIVATE).edit()
            .putBoolean("double_next_seek",enabled).apply();
    }
    /**
     * Explicit user-requested playlist removal. Writes a cloned state first;
     * neither the audio file nor a live playback session is changed if saving fails.
     * The active session order is shortened without re-shuffling survivors.
     */
    boolean removePlaylistTrack(String playlistId,int index,String expectedKey){
        if(recoveryMode){error("Cannot edit playlist while state needs recovery");return false;}
        PlayerState.Playlist playlist=state.playlists.get(playlistId);
        if(playlist==null || index<0 || index>=playlist.entries.size() ||
                !playlist.entries.get(index).equals(expectedKey)){
            error("Playlist changed; reopen before removing a track");return false;
        }
        PlayerState.Progress progress=state.progress(playlist.audiobook);
        boolean wasSelected=playlistId.equals(progress.playlistId) &&
                expectedKey.equals(progress.trackKey);
        boolean activeCurrent=wasSelected && activeBook==playlist.audiobook && player!=null;
        boolean continuePlaying=activeCurrent && (isPlaying() || !prepared);
        final String nextKey=wasSelected?(activeCurrent?
                PlaylistRemovalPolicy.successor(playlist.entries,playbackOrder.snapshot(),
                    expectedKey,repeatMode==PlaylistPlaybackOrder.Repeat.PLAYLIST):
                PlaylistRemovalPolicy.savedSuccessor(playlist.entries,expectedKey)):null;
        try{
            PlayerState updated=StateMutation.prepareAndSave(state,draft->{
                // Validate identity inside the copied transaction, not only above.
                PlayerState.Playlist copy=draft.getPlaylist(playlistId);
                if(index>=copy.entries.size() || !expectedKey.equals(copy.entries.get(index)))
                    throw new IllegalArgumentException("Playlist entry changed");
                draft.remove(playlistId,index);
                if(wasSelected){
                    if(nextKey==null){
                        PlayerState.Progress saved=draft.progress(playlist.audiobook);
                        saved.playlistId="";saved.trackKey="";saved.positionMs=0L;
                    }else draft.select(playlist.audiobook,playlistId,nextKey,0L);
                }
            },this::writeStateBytes);
            if(updated==state){error("Removal was not saved; audio retained");return false;}
            state=updated;
            playbackOrder.removeEntry(playlistId,expectedKey);
            if(activeCurrent){
                releaseAfterCommittedRemoval(continuePlaying && nextKey!=null);
                if(continuePlaying && nextKey!=null){
                    int nextIndex=updated.getPlaylist(playlistId).entries.indexOf(nextKey);
                    if(nextIndex>=0 && !playFromInternal(playlistId,nextIndex,false))
                        error("Track removed, but following track could not open");
                }
            }
            notifyChanged();return true;
        }catch(Exception failure){
            error("Removal not saved: "+failure.getClass().getSimpleName());return false;
        }
    }
    /** Release obsolete MediaPlayer without saving its position into the NEW track. */
    private void releaseAfterCommittedRemoval(boolean continuing){
        transientResumePending=false;
        playbackGate.requestPause();
        abandonFocus();
        MediaPlayer old=player;player=null;prepared=false;awaitingInitialSeek=false;
        if(old!=null){try{old.reset();}catch(Exception ignored){}
            finally{try{old.release();}catch(Exception ignored){}}}
        // An edited playlist continuing with another track owns the same service.
        // Stop/retire only if no successor was chosen.
        if(!continuing)retireForeground();
        updateMediaSession();
    }
    boolean playPlaylist(String playlistId){
        PlayerState.Playlist p=state.playlists.get(playlistId);
        if(p==null || p.entries.isEmpty()){error("Playlist has no tracks");return false;}
        String first=p.entries.get(shuffleEnabled(p.audiobook)?shuffleRandom.nextInt(p.entries.size()):0);
        playbackOrder.start(p.id,p.entries,first,shuffleEnabled(p.audiobook),shuffleRandom);
        return playFromInternal(p.id,p.entries.indexOf(first),false);
    }
    boolean playFrom(String playlistId,int index,boolean resume){
        PlayerState.Playlist p=state.playlists.get(playlistId);
        if(p==null || index<0 || index>=p.entries.size()){error("Playlist entry missing");return false;}
        playbackOrder.start(p.id,p.entries,p.entries.get(index),shuffleEnabled(p.audiobook),shuffleRandom);
        return playFromInternal(playlistId,index,resume);
    }
    /**
     * DEV17: switching tracks is NOT Stop. In particular, never call stopSelf()
     * during completion -> prepareAsync of the next shuffled track while the
     * phone is closed. The foreground service remains alive during handoff.
     */
    private boolean releaseForTrackHandoff(){
        transientResumePending=false;
        savePosition();
        if(!persist())return false;
        abandonFocus();
        MediaPlayer old=player;player=null;prepared=false;awaitingInitialSeek=false;
        if(old!=null){try{old.reset();}catch(Exception ignored){}
            finally{try{old.release();}catch(Exception ignored){}}}
        playbackEvent("old_media_player_released_without_service_stop");
        return true;
    }
    private boolean playFromInternal(String playlistId,int index,boolean resume){
        lastError="";
        if(recoveryMode){error("Saved state requires recovery");return false;}
        PlayerState.Playlist p=state.playlists.get(playlistId);
        if(p==null || index<0 || index>=p.entries.size()){error("Playlist entry missing");return false;}
        String key=p.entries.get(index);
        PlayerState.Track track=state.tracks.get(key);
        if(track==null){error("Track identity missing");return false;}
        long start=0;
        PlayerState.Progress before=state.progress(p.audiobook);
        if(resume && before.playlistId.equals(p.id) && before.trackKey.equals(key))start=before.positionMs;
        // Keep the canonical saved position until playback actually starts.
        final long audibleStart=(resume && p.audiobook)
            ?SleepTimerPolicy.rewindPosition(start,audiobookRewindSeconds):start;
        // Timer follows automatic tracks within the same playlist, but cannot
        // silently act on a newly selected playlist or Music/Audiobook session.
        if(sleepDeadlineElapsed>=0L && (sleepBook!=p.audiobook || !sleepPlaylistId.equals(p.id)))
            clearSleepTimer();
        trackTransitionCount++;
        playbackEvent("track_handoff_begin");
        if(!releaseForTrackHandoff()){
            stopPlayer();error("Previous position could not be saved; playback stopped");return false;
        }
        if(!requestFocus(p.audiobook)){
            retireForeground();error("Audio unavailable during call or interruption");return false;
        }
        final boolean oldBook=activeBook;
        final PlayerState.Progress oldProgress=new PlayerState.Progress(state.progress(p.audiobook));
        activeBook=p.audiobook;playbackGate.requestPlay();
        state.select(activeBook,p.id,key,start);
        if(!persist()){
            state.progress(activeBook).restoreFrom(oldProgress);activeBook=oldBook;
            playbackGate.requestPause();abandonFocus();retireForeground();
            error("Cannot save new selection");return false;
        }
        try{
            MediaPlayer mp=new MediaPlayer();player=mp;prepared=false;
            // MediaPlayer holds the CPU wake lock only while playing; release on pause/stop.
            // If playback ownership changes, review the manifest WAKE_LOCK permission too.
            mp.setWakeMode(getApplicationContext(), PowerManager.PARTIAL_WAKE_LOCK);
            mp.setAudioAttributes(attrs(activeBook));mp.setDataSource(this,Uri.parse(track.uri));
            mp.setOnPreparedListener(ready->{
                if(player!=ready)return;
                prepared=true;
                playbackEvent("on_prepared");
                long at=audibleStart;
                try {
                    if(at>0){
                        awaitingInitialSeek=true;
                        ready.setOnSeekCompleteListener(seeked->{
                        if(player!=seeked)return;
                        try {
                            seeked.setOnSeekCompleteListener(null);
                            awaitingInitialSeek=false;
                            if(canStart()){
                                seeked.start();
                                playbackEvent("playback_started_after_seek");
                                commitAudibleResumePosition(at);
                            }
                            updateMediaSession();notifyChanged();
                        } catch (Exception e) {
                            stopPlayer();restoreFailedSelection(p.audiobook,p.id,key,oldProgress,oldBook);
                            error("Playback could not start");
                        }
                    });ready.seekTo((int)Math.min(Integer.MAX_VALUE,at));}
                    else if(canStart()){
                        awaitingInitialSeek=false;
                        ready.start();
                        playbackEvent("playback_started");
                        commitAudibleResumePosition(at);
                    }
                    updateMediaSession();notifyChanged();
                } catch (Exception e) {
                    stopPlayer();restoreFailedSelection(p.audiobook,p.id,key,oldProgress,oldBook);
                    error("Playback could not prepare");
                }
            });
            mp.setOnCompletionListener(done->{
                if(player!=done || !CompletionPolicy.mayAdvance(playbackGate,focusGate))return;
                playbackEvent("on_completion");
                savePosition();
                if (!persist()) { stopPlayer();error("Position could not be saved; playback stopped");return; }
                // Guard stale completion after playlist edits and focus changes.
                PlayerState.Progress progress=state.progress(p.audiobook);
                PlayerState.Playlist live=state.playlists.get(p.id);
                if(live==null || !p.id.equals(progress.playlistId) || !key.equals(progress.trackKey)){
                    stopPlayer();return;
                }
                if(!playbackOrder.matches(p.id,live.entries,key))
                    playbackOrder.start(p.id,live.entries,key,shuffleEnabled(p.audiobook),shuffleRandom);
                String nextKey=playbackOrder.next(key,1,repeatMode,true);
                if(nextKey==null){stopPlayer();return;}
                int nextIndex=live.entries.indexOf(nextKey);
                if(nextIndex<0 || !state.tracks.containsKey(nextKey)){stopPlayer();return;}
                playFromInternal(live.id,nextIndex,false);
            });
            mp.setOnErrorListener((failed,what,extra)->{
                if(player!=failed)return true;
                boolean early=!prepared;stopPlayer();
                if(early)restoreFailedSelection(p.audiobook,p.id,key,oldProgress,oldBook);
                error("Cannot play this track; original audio was not modified");return true;
            });
            mp.prepareAsync();
            playbackEvent("prepare_async_issued");
            startForegroundService(new Intent(this, KeypadPlaybackService.class));
            showForeground();updateMediaSession();notifyChanged();return true;
        }catch(Exception e){
            stopPlayer();restoreFailedSelection(p.audiobook,p.id,key,oldProgress,oldBook);
            error("Cannot open track: "+e.getClass().getSimpleName());return false;
        }
    }
    private void commitAudibleResumePosition(long startedAt){
        // Only record the rewound offset after MediaPlayer.start() succeeded.
        // Failed prepare/start leaves the previous durable progress available.
        if(startedAt!=state.progress(activeBook).positionMs){
            state.savePosition(activeBook,startedAt);
            if(!persist()){pause();error("Resumed position could not be saved; playback paused");}
        }
    }
    private void restoreFailedSelection(boolean book,String id,String key,PlayerState.Progress previous,boolean previousBook){
        try{
            FailedOpenRollback.Result rollback=FailedOpenRollback.attempt(state,book,id,key,previous,this::writeStateBytes);
            if(rollback.restored()){state=rollback.state;activeBook=previousBook;notifyChanged();}
            else if(rollback.outcome==FailedOpenRollback.Outcome.SAVE_FAILED)error("Failed to durably restore previous session");
        }catch(Exception e){error("Rollback could not finish");}
    }
    void seek(long delta){
        if(!isPrepared())return;
        PlayerState.Progress p=state.progress(activeBook);
        try{long next=state.seek(p.trackKey,position(),delta);seekAbsolute(next);}
        catch(Exception e){error("Seek failed");}
    }
    void seekAbsolute(long requested){
        if(!isPrepared())return;
        try{
            PlayerState.Progress p=state.progress(activeBook);
            long next=state.clamp(p.trackKey,requested);
            player.seekTo((int)Math.min(Integer.MAX_VALUE,next));state.savePosition(activeBook,next);
            persist();updateMediaSession();notifyChanged();
        }catch(Exception e){error("Seek failed");}
    }
    void skip(int delta){
        PlayerState.Progress p=state.progress(activeBook);
        PlayerState.Playlist pl=state.playlists.get(p.playlistId);
        if(pl==null)return;
        if(!playbackOrder.matches(pl.id,pl.entries,p.trackKey))
            playbackOrder.start(pl.id,pl.entries,p.trackKey,shuffleEnabled(activeBook),shuffleRandom);
        String nextKey=playbackOrder.next(p.trackKey,delta,repeatMode,false);
        if(nextKey==null)return;
        int next=pl.entries.indexOf(nextKey);
        if(next>=0)playFromInternal(pl.id,next,false);
    }
    boolean previewFocusGranted(){return focusGate.canStart();}
    boolean requestFocus(boolean book){
        if(audioManager==null)return false;
        int mode=audioManager.getMode();
        if(mode==AudioManager.MODE_RINGTONE || mode==AudioManager.MODE_IN_CALL || mode==AudioManager.MODE_IN_COMMUNICATION){
            abandonFocus();return false;
        }
        abandonFocus();final long epoch=++focusEpoch;
        focusRequest=new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN)
            .setAudioAttributes(attrs(book)).setWillPauseWhenDucked(book)
            .setOnAudioFocusChangeListener(change->{if(epoch==focusEpoch)focusChanged(change);},handler).build();
        boolean granted=audioManager.requestAudioFocus(focusRequest)==AudioManager.AUDIOFOCUS_REQUEST_GRANTED;
        focusGate.onExplicitRequest(granted);if(!granted)abandonFocus();return granted;
    }
    private boolean canStart(){return playbackGate.canStart() && focusGate.canStart();}
    private boolean phoneCallMode(){
        if(audioManager==null)return false;
        int mode=audioManager.getMode();
        return mode==AudioManager.MODE_RINGTONE || mode==AudioManager.MODE_IN_CALL ||
            mode==AudioManager.MODE_IN_COMMUNICATION;
    }
    /**
     * DEV17 focus behavior for BOTH lanes. A temporary notification is permitted
     * to resume only when this *same* session was playing or preparing.
     * Calls can manifest as transient loss on some OEM systems: mode checks are
     * a defensive guard, not complete telephony identification (device test needed).
     */
    private void focusChanged(int change){
        if(change==AudioManager.AUDIOFOCUS_GAIN){
            focusGate.onGain();
            if(!transientResumePending)return; // unsolicited or permanent gain
            transientResumePending=false;
            if(phoneCallMode() || player==null){
                playbackGate.requestPause();focusGate.onLoss();
                abandonFocus();keepPausedControls();updateMediaSession();notifyChanged();return;
            }
            // Only this service's already granted transient focus request may
            // resume. A user Pause/Stop called abandonFocus() and cancelled it.
            playbackGate.requestPlay();
            if(canStart())try{
                if(prepared && !awaitingInitialSeek){
                    player.start();
                    playbackEvent("auto_resumed_after_transient_focus_gain");
                } // pending prepareAsync will start later through canStart().
                showForeground();
            }catch(Exception e){stopPlayer();error("Unable to resume after notification");return;}
            updateMediaSession();notifyChanged();return;
        }
        boolean temporary=(change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT ||
            change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK) && !phoneCallMode();
        if(change!=AudioManager.AUDIOFOCUS_LOSS && !temporary &&
            change!=AudioManager.AUDIOFOCUS_LOSS_TRANSIENT &&
            change!=AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK)return;
        boolean wasRequested=playbackGate.canStart();
        if(temporary){
            transientResumePending|=wasRequested;
            focusGate.onTransientLoss();
        }else{
            transientResumePending=false;
            focusGate.onLoss();
        }
        playbackGate.requestPause();
        if(isPlaying())try{player.pause();}catch(Exception failure){
            stopPlayer();error("Interrupted playback could not pause; player released");return;
        }
        savePosition();
        if(!persist()){
            stopPlayer();error("Position could not be saved; playback stopped");return;
        }
        if(temporary && transientResumePending){
            // Keep the service foreground during the notification. Otherwise
            // Android can terminate it before transient focus returns.
            playbackEvent("transient_focus_paused");
            updateMediaSession();notifyChanged();
        }else{
            // Permanent loss or a detected call is never generic autoplay.
            abandonFocus();keepPausedControls();updateMediaSession();notifyChanged();
        }
    }
    void abandonFocus(){
        transientResumePending=false;
        ++focusEpoch;focusGate.onAbandon();
        if(audioManager!=null && focusRequest!=null)audioManager.abandonAudioFocusRequest(focusRequest);
        focusRequest=null;
    }
    private void updateMediaSession(){
        if(mediaSession==null)return;
        long actions=PlaybackState.ACTION_PLAY|PlaybackState.ACTION_PAUSE|PlaybackState.ACTION_PLAY_PAUSE|
            PlaybackState.ACTION_STOP|PlaybackState.ACTION_SKIP_TO_NEXT|PlaybackState.ACTION_SKIP_TO_PREVIOUS|
            PlaybackState.ACTION_SEEK_TO;
        int status=isPlaying()?PlaybackState.STATE_PLAYING:(isPrepared()?PlaybackState.STATE_PAUSED:PlaybackState.STATE_STOPPED);
        mediaSession.setPlaybackState(new PlaybackState.Builder().setActions(actions)
            .setState(status,position(),isPlaying()?1f:0f,SystemClock.elapsedRealtime()).build());
        // A paused, prepared track still has a visible Play control, even with
        // the Activity closed and no foreground-service notification ownership.
        if(foreground || isPrepared()){
            NotificationManager nm=(NotificationManager)getSystemService(Context.NOTIFICATION_SERVICE);
            nm.notify(NOTIFICATION_ID,notification());
        }
    }
    private Notification notification(){
        Intent launch=new Intent(this,KeypadPlayerActivity.class);
        PendingIntent pending=PendingIntent.getActivity(this,0,launch,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        PlayerState.Progress p=state.progress(activeBook);
        PlayerState.Track t=state.tracks.get(p.trackKey);
        String title=t==null?"Keypad Player":t.title;
        Notification.Action previous=new Notification.Action.Builder(android.R.drawable.ic_media_previous,remoteSeekEnabled(activeBook)?"Back 15s":"Previous track",
            notificationAction(ACTION_PREVIOUS,1)).build();
        Notification.Action toggle=new Notification.Action.Builder(isPlaying()?android.R.drawable.ic_media_pause:android.R.drawable.ic_media_play,
            isPlaying()?"Pause":"Play",notificationAction(ACTION_TOGGLE,2)).build();
        Notification.Action next=new Notification.Action.Builder(android.R.drawable.ic_media_next,remoteSeekEnabled(activeBook)?"Forward 30s":"Next track",
            notificationAction(ACTION_NEXT,3)).build();
        return new Notification.Builder(this,CHANNEL).setSmallIcon(android.R.drawable.ic_media_play)
            .setContentTitle(title).setContentText(isPlaying()?"Playing":"Paused · select Play to resume")
            .setContentIntent(pending).setOngoing(isPlaying() || transientResumePending)
            .addAction(previous).addAction(toggle).addAction(next)
            .setStyle(new Notification.MediaStyle().setMediaSession(mediaSession.getSessionToken())
                .setShowActionsInCompactView(0,1,2)).build();
    }
    private PendingIntent notificationAction(String action,int requestCode){
        Intent intent=new Intent(this,KeypadPlaybackService.class).setAction(action);
        return PendingIntent.getService(this,requestCode,intent,
            PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
    }
    // After a pause (manual or focus interruption), keep a user-visible,
    // non-ongoing media notification with Play and a live MediaSession.
    // Android may still reclaim a nonforeground service; no auto-resume follows.
    private void keepPausedControls(){
        if(recoveryMode || !isPrepared()){retireForeground();return;}
        if(foreground){stopForeground(false);foreground=false;}
        NotificationManager nm=(NotificationManager)getSystemService(Context.NOTIFICATION_SERVICE);
        nm.notify(NOTIFICATION_ID,notification());
    }
    // An explicit Stop or a released/unprepared player removes controls and
    // permits service teardown. A normal pause MUST NOT call this helper.
    private void retireForeground(){
        if (foreground) { stopForeground(true); foreground=false; }
        ((NotificationManager)getSystemService(Context.NOTIFICATION_SERVICE)).cancel(NOTIFICATION_ID);
        stopSelf();
    }
    private void showForegroundForRecovery(){
        startForeground(NOTIFICATION_ID,notification());foreground=true;
        retireForeground();
    }
    private void showForeground(){
        if(recoveryMode)return;
        startForeground(NOTIFICATION_ID,notification());foreground=true;
    }
    private void notifyChanged(){if(listener!=null)listener.onPlaybackChanged();}
    private void error(String msg){lastError=msg;if(listener!=null)listener.onPlaybackError(msg);}
    @Override public void onDestroy(){
        volumeDoubleSeekEnabled=false;handler.removeCallbacks(volumeDoubleSeekPoll);volumeDoubleTap.clear();
        finishBluetoothDiagnostic("Service closed before 45s");clearSleepTimer();handler.removeCallbacks(saveTick);handler.removeCallbacks(mediaFlush);transport.close();stopPlayer();
        if(mediaSession!=null){mediaSession.setActive(false);mediaSession.release();mediaSession=null;}
        ((NotificationManager)getSystemService(Context.NOTIFICATION_SERVICE)).cancel(NOTIFICATION_ID);
        super.onDestroy();
    }
}
