# Dumbplayer DEV11 / 0.2.5 — source-only 45-second Bluetooth diagnostic

**STATUS:** UNBUILT, UNINSTALLED, UNTESTED ON KYOCERA. Retains all DEV10 playlist-import functionality. It is a diagnostic branch for the same Android package `org.roarin.kyocerakeypad.sandboxwqa365`, not a separate app. It must be built with a signing certificate that matches the installed Dumbplayer to preserve app data.

## Owner-selected reference behavior

The same Bluetooth neckband on Podcast Addict (smartphone) gives double Volume Up = **+30 seconds** and double Volume Down = **−15 seconds**, with no observed volume change; Dumbplayer may change volume incidentally and still be useful. Single volume presses should remain ordinary volume adjustments; Play/Pause and hold-Next must continue working. These are the owner's target behaviors, **NOT implemented** in this diagnostic build.

## What DEV11 actually changes

- In Listening settings, **Record Bluetooth volume/keys (45s)** starts only when a track is already playing. Starting the test never touches the player state, files, playlists or audio routing.
- For 45 seconds, the background playback service samples **only the Android music stream's numeric volume index** every 100 ms, recording changes with elapsed milliseconds. It also records any `MediaSession.Callback` media key codes and playback callback names received in that window.
- The final report is a small UTF-8 text file named `bt_probe_<timestamp>.txt` under `/sdcard/Android/data/org.roarin.kyocerakeypad.sandboxwqa365/files/transfer/`. It does not contain track titles, filenames, media contents, BT addresses, device serials or contact data.
- If the Android service stops before 45 seconds, it attempts to save the partial report with an explicit `Service closed before 45s` marker.
- No recording occurs outside the explicit 45-second window. The code does not intercept, remap, delay or suppress any volume / playback command. No hardware polling privileges or special permissions added.

**Important diagnostic limitation:** `AudioManager.getStreamVolume(STREAM_MUSIC)` reflects only system-visible volume changes. Some neckbands handle volume locally or via AVRCP absolute volume, and volume inputs may never reach the app's media-session callbacks. A report with no changes DOES NOT prove that no button presses occurred. The sample interval may combine multiple quick presses into one volume-index step. An instrumented app cannot directly intercept Bluetooth volume in all Android configurations; avoid claiming it can.

## Owner trial (only after GitHub build/install is deliberately approved and signing verified)

1. Install a matching-signed DEV11 APK with `adb install -r ...`. **Never uninstall/clear data to bypass signing errors.** Keep the known-working DEV10 APK available for rollback with matching signer (Android may refuse a version-code downgrade).
2. Connect neckband, play an unimportant track, open **Listening settings → Record Bluetooth volume/keys (45s)**. Close the flip if desired. During the window do: (a) Up once, (b) Up twice quickly, (c) Down once, (d) Down twice quickly, (e) optionally hold Next. Leave about 3 seconds between sets to correlate entries with actions. Controls are not remapped.
3. Connect USB and run in Windows PowerShell:

```powershell
adb devices
adb shell ls -lt '/sdcard/Android/data/org.roarin.kyocerakeypad.sandboxwqa365/files/transfer/bt_probe_*.txt'
# Copy only the newest bt_probe_<timestamp>.txt shown above:
$filename = Read-Host 'Paste the bt_probe_...txt filename (no path)'
$remote = '/sdcard/Android/data/org.roarin.kyocerakeypad.sandboxwqa365/files/transfer/' + $filename
adb pull $remote "$env:USERPROFILE\Downloads\$filename"
```

Please report whether single/double presses changed the Kyocera volume and whether the phone lid was open or closed. Inspect the report before sharing if you prefer; it contains only the limited fields described above.

## Build/test status

- Source candidate based on exact Library DEV10 ZIP: `DUMBPLAYER_DEV10_PC_PLAYLIST_IMPORT_SOURCE_ONLY_20261105.zip` (SHA-256 recorded in build report).
- Source insertion, interaction containment and manifest validation tested via Python static assertions and diff check. Existing DEV10 pure-Java smoke suite may be run and results preserved separately.
- No Android SDK/Gradle build, APK installation, headset trial or runtime capture performed here. **Do not treat this as a proved Bluetooth +30/−15 feature.**
- The Bluetooth diagnostic is a distinct optional branch. Workers should integrate only after checking actual owner headset event evidence. If Android does not expose volume events, investigate ADB/system traces or alternative headset commands before proposing audio-routing mutation.
