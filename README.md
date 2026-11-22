<div align="center">
  <img src="assets/dumbplayer-icon.svg" width="112" height="112" alt="Orange play triangle with a white outline on a navy background">

  # Dumbplayer

  **Music and audiobooks, built for real buttons.**

  A local audio player for Android phones with physical keypads, developed for the Kyocera DuraXA Equip (E4831).

  **Music in orange · Audiobooks in navy**
</div>

Dumbplayer puts the D-pad and physical keys to work. Browse your music, arrange playlists, pick up an audiobook, or skip ahead without reaching for a touchscreen. Your recordings stay on your phone, and the app works offline.

## Features

| Music | Audiobooks |
| --- | --- |
| Browse local songs and build playlists in your own order | Keep listening progress separate from Music |
| Shuffle and repeat controls | Save, browse, rename, and jump to bookmarks |
| Browse the playing playlist and choose another track while audio continues | Quick backward and forward seeks |
| Choose how Bluetooth Next/Previous behaves | Choose Bluetooth behavior independently from Music |

Both modes include keypad navigation, a sleep timer, and persistent playback state. You can browse playlists while listening, rearrange their tracks, and remove a playlist entry while keeping the original audio file.

An optional **manual playlist exchange with a Windows or Linux computer** exports library and playlist metadata as JSON. After editing playlists on your computer, you can import them on the phone with a preview and confirmation step. Audio files stay where they are.

## Playlist Desk for Windows and Linux

[**Playlist Desk**](tools/playlist-desk/README.md) is the companion desktop editor. It helps arrange Music and Audiobook playlists with a full keyboard and mouse. It supports saved-playlist navigation, comma-combined library searches, local artist-first matching, and reviewing possible duplicates. The optional Gemma and MusicBrainz features are described in its own guide.

The phone and desktop exchange playlist metadata as JSON. Export a phone snapshot, edit the playlists on your computer, and transfer `pc_playlist_import_v1.json` back to Dumbplayer for review and import. The [transfer walkthrough](tools/playlist-desk/README.md#move-playlists-between-the-phone-and-computer) covers the steps.

Run Playlist Desk with Python and Tkinter:

- **Windows:** `tools/playlist-desk/src/launch_windows.cmd`
- **Linux:** from `tools/playlist-desk/src/`, run `bash launch_linux.sh` (Python 3.9+ and Tkinter).

The [desktop guide](tools/playlist-desk/README.md) covers both platforms, and the [Linux port notes](tools/playlist-desk/README_LINUX_20261122.md) cover installation and path handling. Playlist Desk has its own [source and bridge checks](.github/workflows/playlist-desk-source-checks.yml).

## Keypad controls

On the **Now Playing** screen:

| Key | Action |
| --- | --- |
| `1` / `3` | Back 10 seconds / forward 10 seconds |
| `4` / `6` | Previous / next track |
| `5` | Play / pause |
| `0` (Audiobooks) | Quick bookmark |
| `7` / `9` (Audiobooks) | Previous / next bookmark |
| `#` (Audiobooks) | Open bookmarks |
| Back | Return to the menu while playback continues |

On **Home**, number keys `1`–`9` open the corresponding menu item, and `*` opens menu reordering. In playlist move mode, Up/Down adjusts a track's position, `1`/`9` moves it to the top/bottom, Center saves, and Back/CLR cancels.

### Headsets and Bluetooth

The app can interpret standard Bluetooth **Next/Previous** commands differently for Music and Audiobooks. The defaults are:

- **Music:** previous or next track.
- **Audiobooks:** back **15 seconds** or forward **30 seconds**.

You can change each mode's behavior from its Now Playing controls. Headsets vary in the media commands they send; volume-button and double-tap behavior will depend on the particular device.

## Current source

**DEV17** brings together the latest keypad, playlist, and audiobook features with some newer work on playback continuity and appearance:

- **Track changes:** the player keeps its foreground service active while it prepares the next recording.
- **Short interruptions:** a playing Music or Audiobook session can pause for transient audio-focus loss and resume from its saved position when focus returns. Manual Pause and Stop remain under your control.
- **Appearance:** orange for Music, navy for Audiobooks, and a white-outlined orange play triangle on navy for the app icon. Shared screens use neutral styling and clear labels.

The host-side Java and source checks have passed. **GitHub Actions compilation, signing, and DEV17 testing on the physical Kyocera are still pending.** Hardware testing will be especially useful for closed-phone shuffle, notification sounds, calls, and Bluetooth controls.

For implementation details, see the [DEV17 release notes](RELEASE_NOTES_DEV17_20261122.md), [DEV16–DEV17 change ledger](DEV16_TO_DEV17_SOURCE_CHANGE_LEDGER.json), and [test results](DEV17_TEST_RESULTS.json).

## Build with GitHub Actions

The source targets **Android 10 (API 29)**, with **Java 17**, **Android SDK 33**, **Gradle 7.6.4**, and **Android Gradle Plugin 7.4.2**.

1. Upload the full source tree to a GitHub repository, keeping `app/`, `tests/`, and `.github/workflows/` in place.
2. Open **Actions** and select [**Dumbplayer DEV17 integrated unsigned candidate**](.github/workflows/dev17-unsigned-local-sign.yml).
3. Choose **Run workflow**, then download the `dumbplayer-dev17-UNSIGNED-LOCAL-SIGNING-REQUIRED` artifact after a successful build.
4. Sign the resulting APK locally with Android SDK tools. To update an existing installation and keep its data, use the **same signing certificate** as the installed app.

The [DEV17 build guide](00_START_HERE_GITHUB_DEV17_20261122.md) includes the GitHub upload steps, signing commands, and certificate verification instructions.

To run the host-side checks on a computer with the necessary tools:

```bash
bash tests/run_dev17_source_smoke.sh
```

The workflow downloads the required Gradle version. This source package contains the current DEV17 workflow alongside historical project documentation.

## Compatibility and feedback

Development and device testing have centered on the Kyocera DuraXA Equip (E4831). Other keypad-operated Android phones may work, with their own key mapping and audio-format support. The current audio decoder support comes from the Android device; M4B support has yet to be established.

If you try the app, useful reports include your phone model, Android version, the physical key or headset command used, and what happened. Sanitized logs are welcome; personal audio and playlist filenames can stay private.

## License

The repository includes the [Apache License 2.0](LICENSE) for original Dumbplayer source and documentation where the relevant contributors hold the licensing rights. [License scope and third-party notes](LICENSE_SCOPE.md) cover the details, including historical code and dependencies.
