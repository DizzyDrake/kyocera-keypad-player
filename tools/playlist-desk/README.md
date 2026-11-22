# Playlist Desk

**A Windows and Linux companion for Dumbplayer.** Browse and rearrange playlists using your computer, then send the edited playlist list back to your phone.

Playlist Desk runs locally with Python and Tkinter. It works with the `kyocera-phone-snapshot-v0.1-PROVISIONAL` metadata export produced by Dumbplayer. The November 15 integrated source includes saved-playlist next/previous navigation, comma-combined library searches, local full-artist-credit matching, optional Gemma 4 matching, a bounded possible-duplicate review, and guarded metadata imports. Possible duplicates are presented for manual review, with the audio files left untouched.

## Start Playlist Desk

### Windows

1. Install Python 3 with Tkinter (regular Windows Python includes it).
2. Open `src/launch_windows.cmd` in this folder.
3. Try the included `src/sample/dev8_fictional_phone_export.json` for a first look.

### Linux

1. Install Python 3.9+ and Tkinter using your distribution packages (`python3` and `python3-tk` on Debian/Ubuntu, `python3-tkinter` on Fedora).
2. From `tools/playlist-desk/src/`, run `bash launch_linux.sh` in a graphical desktop session.
3. Try `src/sample/fictional_phone_snapshot.json` first.

The [Linux port guide](README_LINUX_20261122.md) covers the launcher, desktop requirements, and path handling. The November 22 Linux source passed 249 unit tests and 10 Xvfb/Tk GUI checks. A native Windows launch, a physical Linux desktop, the owner's music library, and optional local models remain to be checked.

## Move playlists between the phone and the computer

1. In Dumbplayer, export the current library and playlist metadata. The phone saves a `phone_snapshot_<unique-id>.json` file under its app-specific `transfer` folder.
2. On your computer, use ADB to pull that exact snapshot. For the package ID in this source, the on-device folder is `/sdcard/Android/data/org.roarin.kyocerakeypad.sandboxwqa365/files/transfer/`. You can list its files with:

   ```bash
   adb shell ls /sdcard/Android/data/org.roarin.kyocerakeypad.sandboxwqa365/files/transfer/
   ```

3. Open the snapshot in Playlist Desk, edit and save your playlists, and use **Create phone import JSON…**. The output name is `pc_playlist_import_v1.json`.
4. Transfer the file into the same app-specific `transfer` folder on the phone:

   ```bash
   adb push pc_playlist_import_v1.json /sdcard/Android/data/org.roarin.kyocerakeypad.sandboxwqa365/files/transfer/pc_playlist_import_v1.json
   ```

5. On the phone, choose the PC playlist import, read the preview, and confirm the replacement when the proposed playlists look right. The app keeps the audio files and bookmarks. Some listening positions may reset after changing playlists.

The file transfer is manual. Keep a copy of the original phone snapshot and edited PC JSON until you've checked the result. If Android reassigns media IDs or a file is missing, the phone reports unresolved entries during the import preview. The phone can preview a stale snapshot import, while Playlist Desk requires its edited JSON to match the snapshot used to create it.

## Matching and review

- **Music:** saved-playlist navigation, playlist ordering, comma-separated search terms, local artist-first and optional Gemma 4 matches.
- **Audiobooks:** independent playlist category and metadata transfer.
- **Possible duplicates:** review normalized metadata candidates in manageable pages. Audio-file identity and actual playback equivalence still require manual examination.
- **Optional MusicBrainz:** performs only an explicit search using the artist and title you enter; see the inherited source README for details.

The requested button and color refinements remain part of future Playlist Desk UI work. The desktop interface is retained in this source.

## Source checks

From the repository root:

```bash
python tools/playlist-desk/VERIFY_INTEGRATED_SOURCE.py
cd tools/playlist-desk/src
python -m unittest discover -s tests -p "test_*.py"
```

Phone/desktop schema checks live in `tools/playlist-desk/tests/test_dumbplayer_bridge_contract.py`; the [GitHub Actions workflow](../../.github/workflows/playlist-desk-source-checks.yml) runs them alongside the Python tests and Linux GUI smoke test. You can run the GUI test locally with `PYTHONPATH=tools/playlist-desk/src xvfb-run -a python3 tools/playlist-desk/src/tests/gui_linux_port.py` when Xvfb is installed.

**Build status:** Source-ready desktop application, launched directly from Python on Windows and Linux. The Android application retains its separate DEV17 unsigned-APK workflow and private signing process.

## Provenance and licensing

This edition uses the [November 22 Linux port](README_LINUX_20261122.md) of the November 15 Playlist Desk baseline. It adds the Linux launcher, Linux path handling, and associated tests while retaining the Windows launcher and the existing playlist formats. The Linux port source ZIP is `PLAYLIST_DESK_LINUX_SOURCE_FROM_20261115_20261122.zip` (SHA-256 `f6887fad6eb120a450405c966a265371ba38e83a887b4a61fcb15f786dea79ea`). Its original source reports and change patch are included. The phone/desktop bridge contract tests were carried over from the existing DEV17 companion package.

See the repository [LICENSE](../../LICENSE) and [license scope](../../LICENSE_SCOPE.md), plus the source package's `README_WQB390_GUARDED_CANDIDATE.md`. Third-party tools and services retain their own terms.
