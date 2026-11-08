# Dumbplayer DEV12 — opt-in double-volume seek source-only experiment

**Status:** SOURCE ONLY. Based on DEV11 Bluetooth volume diagnostic. The owner supplied three real Kyocera probe reports on November 8, 2026. No Android Gradle/APK build or live DEV12 phone trial has been performed here. Existing DEV10/DEV11 installed state is untouched.

## Owner-confirmed behavior

- Monster Airmars SG03 Pro used on both phone models.
- Double Volume Up = **seek +30 s**, double Volume Down = **seek −15 s** (Podcast Addict target).
- Normal single presses remain ordinary volume changes; incidental volume adjustment on double press is acceptable.
- Existing hold-Next and Play/Pause must keep working.

## What this candidate implements

Listening settings → **Experimental double VOLUME seek: OFF/ON**, **OFF by default**. While audio is playing, the existing foreground playback service reads `AudioManager.getStreamVolume(STREAM_MUSIC)` every 100 ms. Two observed consecutive one-index increments/decrements in the same direction within 650 ms request a +30 s/−15 s seek. After a successful pair there is an 850 ms cooldown. The service backs off to 500 ms sampling when not playing, resets on pause, skips detection while the 45-second diagnostic records, and cancels callbacks at service shutdown. No volume override, remote VolumeProvider, new permission, notification, or extra app/package ID. Original media transport source is unchanged.

This mechanism detects **volume level changes, not specific headset buttons**: fast adjustment with physical Kyocera buttons can also trigger it; a held button could be mistaken for presses. At minimum/maximum volume, when Android applies no change, no seek is possible. Multiple changes merged into one poll are deliberately ignored to limit false positive seeks. The trial may require tuning or reversal. The on-device setting explains these limitations and may be switched OFF immediately.

The DEV11 diagnostic still records on explicit request for 45 seconds; this candidate suspends seeking during the recording. Reports are written in the app-specific shared-storage `transfer` folder using `getExternalFilesDir("transfer")`; `/sdcard` is usually Android's alias for main shared internal storage, not a physical SD card.

## Source-only validation and limitations

`tests/run_bluetooth_volume_seek_smoke.sh` runs inherited DEV9/DEV11 smoke checks, new pure Java detector fixtures (including two replayed actual probe sequences), and source wiring assertions. Passing tests do not establish Android compile, Android volume routing on all devices, flip-closed behavior, Bluetooth timing accuracy, headset-vs-local-button discrimination, or owner approval of UX. The existing playlist import is inherited unmodified; no owner audio or playlists were bundled.

Install only after building and checking the Android APK signature against installed app. **Never uninstall or clear data to work around a signing mismatch**. Preserve the current working APK and local playlists. Build target API 33 / min API 29 and installed package `org.roarin.kyocerakeypad.sandboxwqa365` are unchanged.
