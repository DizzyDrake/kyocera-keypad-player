# Kyocera PC Playlist Desk + Bridge v0.10 — M3U/M3U8 local reconstruction

**Offline, source-only incremental candidate.** Existing shared queue item `WQ-20261030-012`, session WQB446. This extends WQB445 v0.9; that original ZIP and its README/manifest remain preserved. Python 3.9+ with Tkinter; Windows 10 is the target, **not yet physically tested**. No phone importer, ADB round-trip, actual audio transfer or deployment is claimed.

## New functionality

The existing **Review local playlist matches** dialog now accepts user-provided `.m3u` and `.m3u8` text files, as well as pasted `#EXTM3U` / `#EXTINF` lists. It retains the prior CSV/TXT, artist/album filter, and opt-in localhost Gemma tabs. No website URL is fetched, and imported media paths are **never opened, copied or played**. The imported text is a source for metadata matching only.

- Exact relative path match to the already loaded metadata can select a real local ID. Paths with `./` prefixes or backslashes are compared as text, never resolved on disk.
- When no exact path matches, an `#EXTINF` `Artist - Title` label can match local metadata. Duplicate editions stay **AMBIGUOUS** and require owner selection.
- Filename-only candidates are marked **REVIEW** even if unique, requiring explicit selection with **Use this ID**. If an exact path conflicts with `#EXTINF` artist/title, the row also requires manual review.
- Missing songs remain **MISSING**; no IDs are invented. The order of M3U entries is preserved, duplicate IDs are skipped with counts. Preview, Apply confirmation, Undo and separate Save As remain in force.
- The UI permits a bounded local file (100 KB / 100,000 characters, up to 1,000 entries). The file selection retains the existing protected-drive guard. File format detection uses `.m3u` / `.m3u8` for imported files and `#EXTM3U` / `#EXTINF` for pasted text. When replacing an imported M3U with unrelated manually pasted CSV, reopen the CSV/TXT file to reset the import-format hint.

## Disposable Windows 10 trial using only fictional data

1. Extract to a temporary folder **not on F:** and run `launch_windows.cmd`. Load `sample/fictional_phone_snapshot.json` (the same fictional sample as v0.9), create a **New Music** playlist named `M3U trial` and select it.
2. Open **Review local playlist matches**, select **Rebuild pasted playlist**, click **Open CSV/TXT/M3U/M3U8**, and choose `sample/fictional_external_playlist.m3u8`. Click **Preview local list**. Expect two MATCH rows (Álpha, Beta) and one MISSING row, with the intended order. The `https://example.invalid` entry is not fetched.
3. Confirm **Append reviewed matches**, check two local IDs added in order, then Undo. For a filename-only path such as `Chapter01.mp3`, expect REVIEW with an actual candidate but no auto-selection; choose **Use this ID** if appropriate. Do not test with real owner media or phone imports yet.

## Provenance and test boundaries

Parent WQB445 ZIP SHA-256 `2b0161f14966c7ce6246d5ad5d63d2146ac557671a1e5e8965399c74ccd5e64c`. Unit tests and Linux Tk/Xvfb GUI smoke passed on fictional metadata, including inherited selection, artist/album matching, drag/drop and local Gemma synthetic-response tests. No Windows installation, real phone export, external website, actual Ollama model, audio files, F: access, or Android device was used. This is **not a final owner-accepted release**.

Low-priority MusicBrainz and local audio/mood enhancements remain **ACTIVE**, not held. The owner's Windows v0.6 trial is the latest confirmed physical PC behavior, not proof this v0.10 candidate is installed.
