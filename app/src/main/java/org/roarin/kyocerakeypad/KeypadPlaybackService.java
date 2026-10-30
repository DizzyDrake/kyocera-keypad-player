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
    private boolean shuffleEnabled, experimentalDoubleNext;
    private PlaylistPlaybackOrder.Repeat repeatMode = PlaylistPlaybackOrder.Repeat.OFF;
    final IBinder binder = new LocalBinder();
    final Handler handler = new Handler(Looper.getMainLooper());
    PlayerState state = new PlayerState();
    boolean recoveryMode, activeBook, prepared;
    MediaPlayer player;
    private AtomicFile store;
    private AudioManager audioManager;
    private AudioFocusRequest focusRequest;
    private final PlaybackGate playbackGate = new PlaybackGate();
    private final AudioFocusGate focusGate = new AudioFocusGate();
    private long focusEpoch;
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
        shuffleEnabled=settings.getBoolean("shuffle",false);
        String savedRepeat=settings.getString("repeat","OFF");
        try { repeatMode=PlaylistPlaybackOrder.Repeat.valueOf(savedRepeat); }
        catch (IllegalArgumentException ignored) { repeatMode=PlaylistPlaybackOrder.Repeat.OFF; }
        experimentalDoubleNext=settings.getBoolean("double_next_seek",false);
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
            @Override public void onPlay(){ explicitPlay(); }
            @Override public void onPause(){ pause(); }
            @Override public void onStop(){ stopPlayer(); }
            @Override public void onSkipToNext(){ skip(1); }
            @Override public void onSkipToPrevious(){ skip(-1); }
            @Override public void onSeekTo(long pos){ seekAbsolute(pos); }
            @Override public boolean onMediaButtonEvent(Intent eventIntent){
                KeyEvent key=eventIntent==null?null:eventIntent.getParcelableExtra(Intent.EXTRA_KEY_EVENT);
                if(key==null)return false;
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
    }
    @Override public int onStartCommand(Intent intent,int flags,int startId) {
        // A foreground-service start is issued only on explicit Play/Resume.
        // Start foreground promptly even while MediaPlayer prepares asynchronously.
        if (!recoveryMode){
            showForeground();
            String action=intent==null?null:intent.getAction();
            if(ACTION_TOGGLE.equals(action))toggle();
            else if(ACTION_NEXT.equals(action))skip(1);
            else if(ACTION_PREVIOUS.equals(action))skip(-1);
            // A pending start may arrive after Play failed or was paused. Honor
            // the foreground deadline first, then retire the idle start.
            if (player == null || !playbackGate.canStart()) retireForeground();
        } else { showForegroundForRecovery(); stopSelf(startId); }
        return START_NOT_STICKY; // Never automatically resume after process death.
    }
    private static MediaTransportSequencer.Key mapMediaKey(int code){
        switch(code){
            case KeyEvent.KEYCODE_MEDIA_PLAY: return MediaTransportSequencer.Key.PLAY;
            case KeyEvent.KEYCODE_MEDIA_PAUSE: return MediaTransportSequencer.Key.PAUSE;
            case KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE:
            case KeyEvent.KEYCODE_HEADSETPHOOK: return MediaTransportSequencer.Key.PLAY_PAUSE;
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
            case NEXT: skip(1);break;
            case PREVIOUS: skip(-1);break;
            case STOP: stopPlayer();break;
            case SEEK_FORWARD_10S: seek(10000);break;
            case SEEK_BACK_10S: seek(-10000);break;
        }
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
        playbackGate.requestPause();savePosition();boolean saved=persist();abandonFocus();
        MediaPlayer old=player;player=null;prepared=false;
        if(old!=null){try{old.reset();}catch(Exception ignored){}finally{try{old.release();}catch(Exception ignored){}}}
        retireForeground();updateMediaSession();notifyChanged();return saved;
    }
    void pause(){
        playbackGate.requestPause();
        if(isPlaying())try{player.pause();}catch(Exception failure){
            stopPlayer();error("Playback could not pause; player released");return;
        }
        savePosition();if (!persist()) error("Position could not be saved");
        abandonFocus();retireForeground();updateMediaSession();notifyChanged();
    }
    void explicitPlay(){
        if(!isPrepared())return; // Never start from stale saved progress alone.
        if(requestFocus(activeBook)){
            playbackGate.requestPlay();
            try {
                if (!canStart()) { retireForeground(); return; }
                player.start();
                startForegroundService(new Intent(this, KeypadPlaybackService.class));
                showForeground();
            } catch(Exception e) {
                // Starting audio may have succeeded before the service start failed.
                // Release it so a reported failure cannot leave unowned audio running.
                stopPlayer();error("Playback could not resume");
            }
        }else error("Audio unavailable during interruption; remains paused");
        updateMediaSession();notifyChanged();
    }
    void toggle(){if(isPlaying())pause();else explicitPlay();}
    // Snapshot for display only. Playback order is service-owned and not re-shuffled by UI renders.
    List<String> playbackOrderSnapshot(){return playbackOrder.snapshot();}
    boolean shuffleEnabled(){return shuffleEnabled;}
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
    void setShuffle(boolean enabled){
        shuffleEnabled=enabled;
        getSharedPreferences("playlist_playback_options_v1",MODE_PRIVATE).edit().putBoolean("shuffle",enabled).apply();
        PlayerState.Progress progress=state.progress(activeBook);
        PlayerState.Playlist p=state.playlists.get(progress.playlistId);
        if (p!=null && p.entries.contains(progress.trackKey))
            playbackOrder.start(p.id,p.entries,progress.trackKey,shuffleEnabled,shuffleRandom);
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
        if(!shuffleEnabled && p!=null && playlistId.equals(progress.playlistId) &&
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
    boolean playPlaylist(String playlistId){
        PlayerState.Playlist p=state.playlists.get(playlistId);
        if(p==null || p.entries.isEmpty()){error("Playlist has no tracks");return false;}
        String first=p.entries.get(shuffleEnabled?shuffleRandom.nextInt(p.entries.size()):0);
        playbackOrder.start(p.id,p.entries,first,shuffleEnabled,shuffleRandom);
        return playFromInternal(p.id,p.entries.indexOf(first),false);
    }
    boolean playFrom(String playlistId,int index,boolean resume){
        PlayerState.Playlist p=state.playlists.get(playlistId);
        if(p==null || index<0 || index>=p.entries.size()){error("Playlist entry missing");return false;}
        playbackOrder.start(p.id,p.entries,p.entries.get(index),shuffleEnabled,shuffleRandom);
        return playFromInternal(playlistId,index,resume);
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
        if(!stopPlayer()){error("Previous position could not be saved; playback stopped");return false;}
        if(!requestFocus(p.audiobook)){error("Audio unavailable during call or interruption");return false;}
        final boolean oldBook=activeBook;
        final PlayerState.Progress oldProgress=new PlayerState.Progress(state.progress(p.audiobook));
        activeBook=p.audiobook;playbackGate.requestPlay();
        state.select(activeBook,p.id,key,start);
        if(!persist()){
            state.progress(activeBook).restoreFrom(oldProgress);activeBook=oldBook;
            playbackGate.requestPause();abandonFocus();error("Cannot save new selection");return false;
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
                long at=audibleStart;
                try {
                    if(at>0){ready.setOnSeekCompleteListener(seeked->{
                        if(player!=seeked)return;
                        try {
                            seeked.setOnSeekCompleteListener(null);
                            if(canStart()){
                                seeked.start();
                                commitAudibleResumePosition(at);
                            }
                            updateMediaSession();notifyChanged();
                        } catch (Exception e) {
                            stopPlayer();restoreFailedSelection(p.audiobook,p.id,key,oldProgress,oldBook);
                            error("Playback could not start");
                        }
                    });ready.seekTo((int)Math.min(Integer.MAX_VALUE,at));}
                    else if(canStart()){
                        ready.start();
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
                savePosition();
                if (!persist()) { stopPlayer();error("Position could not be saved; playback stopped");return; }
                // Guard stale completion after playlist edits and focus changes.
                PlayerState.Progress progress=state.progress(p.audiobook);
                PlayerState.Playlist live=state.playlists.get(p.id);
                if(live==null || !p.id.equals(progress.playlistId) || !key.equals(progress.trackKey)){
                    stopPlayer();return;
                }
                if(!playbackOrder.matches(p.id,live.entries,key))
                    playbackOrder.start(p.id,live.entries,key,shuffleEnabled,shuffleRandom);
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
            mp.prepareAsync();startForegroundService(new Intent(this, KeypadPlaybackService.class));showForeground();updateMediaSession();notifyChanged();return true;
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
            playbackOrder.start(pl.id,pl.entries,p.trackKey,shuffleEnabled,shuffleRandom);
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
            .setAudioAttributes(attrs(book)).setWillPauseWhenDucked(true)
            .setOnAudioFocusChangeListener(change->{if(epoch==focusEpoch)focusChanged(change);},handler).build();
        boolean granted=audioManager.requestAudioFocus(focusRequest)==AudioManager.AUDIOFOCUS_REQUEST_GRANTED;
        focusGate.onExplicitRequest(granted);if(!granted)abandonFocus();return granted;
    }
    private boolean canStart(){return playbackGate.canStart() && focusGate.canStart();}
    private void focusChanged(int change){
        if(change==AudioManager.AUDIOFOCUS_GAIN){focusGate.onGain();return;}
        if(change==AudioManager.AUDIOFOCUS_LOSS || change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT ||
                change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK){
            focusGate.onLoss();playbackGate.requestPause();
            if(isPlaying())try{player.pause();}catch(Exception failure){
                stopPlayer();error("Interrupted playback could not pause; player released");return;
            }
            savePosition();if (!persist()) error("Position could not be saved");
            abandonFocus();retireForeground();updateMediaSession();notifyChanged();
            // Focus GAIN deliberately cannot clear the explicit-interruption latch.
        }
    }
    void abandonFocus(){
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
        if(foreground){NotificationManager nm=(NotificationManager)getSystemService(Context.NOTIFICATION_SERVICE);
            nm.notify(NOTIFICATION_ID,notification());}
    }
    private Notification notification(){
        Intent launch=new Intent(this,KeypadPlayerActivity.class);
        PendingIntent pending=PendingIntent.getActivity(this,0,launch,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        PlayerState.Progress p=state.progress(activeBook);
        PlayerState.Track t=state.tracks.get(p.trackKey);
        String title=t==null?"Keypad Player":t.title;
        Notification.Action previous=new Notification.Action.Builder(android.R.drawable.ic_media_previous,"Previous",
            notificationAction(ACTION_PREVIOUS,1)).build();
        Notification.Action toggle=new Notification.Action.Builder(isPlaying()?android.R.drawable.ic_media_pause:android.R.drawable.ic_media_play,
            isPlaying()?"Pause":"Play",notificationAction(ACTION_TOGGLE,2)).build();
        Notification.Action next=new Notification.Action.Builder(android.R.drawable.ic_media_next,"Next",
            notificationAction(ACTION_NEXT,3)).build();
        return new Notification.Builder(this,CHANNEL).setSmallIcon(android.R.drawable.ic_media_play)
            .setContentTitle(title).setContentText(isPlaying()?"Playing":"Paused · select Play to resume")
            .setContentIntent(pending).setOngoing(isPlaying())
            .addAction(previous).addAction(toggle).addAction(next)
            .setStyle(new Notification.MediaStyle().setMediaSession(mediaSession.getSessionToken())
                .setShowActionsInCompactView(0,1,2)).build();
    }
    private PendingIntent notificationAction(String action,int requestCode){
        Intent intent=new Intent(this,KeypadPlaybackService.class).setAction(action);
        return PendingIntent.getService(this,requestCode,intent,
            PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
    }
    // A bound Activity retains a paused player while visible. If unbound, the
    // stopped service can be destroyed; a later resume uses durable state.
    private void retireForeground(){
        if (foreground) { stopForeground(true); foreground=false; }
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
        clearSleepTimer();handler.removeCallbacks(saveTick);handler.removeCallbacks(mediaFlush);transport.close();stopPlayer();
        if(mediaSession!=null){mediaSession.setActive(false);mediaSession.release();mediaSession=null;}
        super.onDestroy();
    }
}
