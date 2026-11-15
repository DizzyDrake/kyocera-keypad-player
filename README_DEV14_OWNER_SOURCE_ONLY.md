# Dumbplayer DEV14 — active-playlist navigation and separate shuffle

**November 11, 2026 · Source-only implementation candidate (not compiled, signed, installed, or owner-tested).** Continue on DEV13 R2 full source with the DEV13 R3 ten-file overlay. Keep the currently working signed Dumbplayer installed and preserve its data, playlists, bookmarks and transfer folder.

## Owner's observations and requested changes

Owner confirms the actual installed Dumbplayer is wonderful during use at work. She requests independent music-vs-audiobook shuffle; opening/navigating the full currently playing playlist and removing entries including the current track; a way to reach playlists/home without stopping playback; and removing “Experimental double NEXT” and “Record Bluetooth volume/keys” from the ordinary app (debug edition optional).

## Source implementation

- Music and audiobook shuffle are separate **listening categories**, retained as `shuffle_music` and `shuffle_book` in existing private SharedPreferences. On first upgrade, both inherit the old single `shuffle` value; toggling one thereafter never changes the other. Saved playlist order is never shuffled in storage.
- Now Playing → **View playing playlist (keeps playing)**. Focusable D-pad list shows the full active playlist, marks the current track and uses the existing session shuffle order when valid, otherwise saved order. Center opens Play / Remove track actions. Selecting Play is explicit.
- Now Playing **Back** and **Main menu** no longer call `pause`. Home shows an ephemeral **Return to Now Playing** row while audio is prepared. The saved nine-entry home menu and its digit shortcuts/reorder remain intact. Physical Android HOME-key delivery and external system activity behavior are unverified.
- Removal works from either standard playlist track actions or the new active list. It asks for confirmation and removes the **playlist entry only**; original local audio is never deleted. Service validates exact track identity and writes a detached PlayerState through the existing AtomicFile writer before changing playback. Removing a noncurrent entry preserves audio and shrinks active shuffle order without reshuffling. Removing the current entry releases its old MediaPlayer without saving its position into the next track; if audio was playing, it advances to the next available entry in current session order when one exists. With repeat OFF and removal at the final entry, playback stops. Removing the last entry clears its playback context. A paused current-track removal prepares the next saved selection for an explicit Play action; no unexpected autoplay on resume or process restart.
- `Experimental double NEXT` and `Record Bluetooth volume/keys` are visible only when the app is **built as DEBUG**. Normal release builds hide them; old saved double-NEXT preference is not activated on release. Existing user-controlled **double VOLUME** seek remains in Listening settings (Volume Down +30s / Volume Up −15s), unchanged.
- Source version becomes `0.2.8-dev14-playlist-navigation` / versionCode 17; package ID remains `org.roarin.kyocerakeypad.sandboxwqa365` for a possible future same-key update.

## Implementation decisions, not extra owner requirements

Separate shuffle settings are per music/audiobook category (not per individual playlist); the old value is inherited once for each to avoid surprising upgrade changes. When deleting the current playing track, advance to the following entry **only when it exists according to the current playback order and repeat mode**; otherwise stop. These are provisional product choices based on the request, not newly imposed owner rules. Owner can revise them.

## Tests and gaps

- Current source-only regression suites for Bluetooth Volume seek, DEV9/DEV13 integration, imports and lifecycle pass. Synthetic pure Java removal tests and source wiring checks pass. Original source lineage is unchanged in Library.
- The original `tests/run_core_tests.sh` legacy activity-only guard remains incompatible with the existing service architecture and with the owner-updated Home navigation; it was already known to fail in DEV13, not silently treated as passing here. See `DEV14_TEST_LOG.md` and captured logs.
- **No Android Gradle compile, E4831 key/movement test, Bluetooth real-world test of changed build, in-place signing compatibility test, or real playlist removal has occurred.** Do not install, uninstall, sign or release based solely on these offline tests.
- `.github/workflows/dev14-unsigned-local-sign.yml` is an **optional, manually triggered** future source workflow; it generates an **unsigned** APK only and verifies versionCode 17 and package ID. It does not contain or request the private key. A compatible in-place update still requires Aurora to sign the artifact *locally with the permanent key used for her installed DEV13* and verify the certificate before installation; DEV12's older signer is incompatible. No GitHub workflow was executed here.

## Applying the changed-files ZIP

Starting from the original GitHub project containing the exact DEV13 R2 base plus the DEV13 R3 ten-file overlay, copy **only the repository-relative files** in this ZIP over the matching paths, adding new files. Do not blindly replace a different/newer GitHub revision. `SOURCE_MANIFEST.json` describes the resulting full tree and `DEV14_CHANGED_FILE_HASHES.json` describes only the included patch files. Run the offline regression scripts, then use the source-only compilation workflow when the owner is ready. Preserve backups and installed app; no automated signing or deployment.

**Provenance:** `/FOSS/Kyocera Music Player and Playlist Sync/43_DEV13_R3_CHANGED_FILES_ONLY_20261108_POINTER.md`; original source ZIPs remain archived in their historical Library locations. Work Queue parent WQ-20261023-137 remains ACTIVE_ELIGIBLE and DEFAULT.
