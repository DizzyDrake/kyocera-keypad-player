# CURRENT SOURCE CANDIDATE — November 10, 2026 (comma search)

**Read `README_CURRENT_20261110_COMMA_FILTER.md` first.** It describes the added comma-combined Library filter and verified synthetic tests. The earlier November 10 full-credit source and older README/manifest records remain preserved below, as historical source provenance. This candidate is not installed or owner-accepted.

---

# CURRENT SOURCE CANDIDATE — November 10, 2026

**Read `README_CURRENT_20261110_STRICT_ARTIST_CREDIT.md` first.** It explains the integrated strict full-artist-credit correction and synthetic verification. The November 8 candidate and its historical descriptions remain preserved below. The owner's working installation and local music were not accessed.

---

# CURRENT SOURCE CANDIDATE — November 8, 2026

**Start with `README_GEMMA4_ARTIST_FIRST_20261108.md` for the current artist-first/Gemma4 correction.** The versioned notes below are *inherited historical descriptions*, not this candidate's verification report. The untouched parent is WQB164; no Windows installation has been changed.

---

# Kyocera PC Playlist Desk + Bridge v0.15 — optional MusicBrainz recording lookup

**Offline source-only candidate WQD166, November 1, 2026.** Extends WQB458 v0.14 without changing its playlist data model, file operations, drop marker, selection, CSV/M3U matching or PC-only file reuse. The owner-tested PC build remains v0.6; no owner Windows 10, MusicBrainz service, phone or audio trial has been performed on this candidate.

In **Review local playlist matches**, open the new **MusicBrainz (optional)** tab, type an artist and recording title yourself, and click **Search MusicBrainz (internet)**. Only these two explicitly typed terms plus the contact URL/email you enter (required by MusicBrainz for the User-Agent) are sent in a bounded HTTPS request; the app never uploads the loaded track catalog, paths, IDs, filenames or phone metadata. Up to ten recording candidates with artist credits, release titles and MusicBrainz IDs are displayed. Select one and click **Compare selected recording with local tracks** to see exact local metadata matches. Multiple editions remain ambiguous; missing tracks remain missing. No playlist changes occur until the existing explicit **Append reviewed matches** confirmation, and Save As remains separate. No automatic phone write.

**Experimental online limitation:** This candidate was tested only against mocked MusicBrainz JSON, not the live service. MusicBrainz requires a meaningful User-Agent containing a contact URL/email; this candidate requires the user to supply one in the optional tab, never guesses or saves it. Calls are limited to one every 1.1 seconds, and redirects are refused. The live service may still reject or throttle requests. There is no background refresh, no bulk catalog lookup, no API key, no cached personal data, and no automatic retries. Official API policy: https://musicbrainz.org/doc/MusicBrainz_API and https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting. The offline artist/album, pasted list and local Gemma features remain usable without internet.

For a disposable Windows 10 trial, load `sample/fictional_phone_snapshot.json`, open **Review local playlist matches**, and inspect the new tab without clicking Search: no network request occurs. For the first online trial, enter only public fictional/sample artist/title terms you choose and a contact URL/email you are comfortable transmitting to MusicBrainz, click Search once, select a result and Compare. Check whether MusicBrainz responds, whether candidates are intelligible and whether local matching reports MATCH/AMBIGUOUS/MISSING. Do not use personal media, phone sync, or `F:\`. This is optional and low-priority ACTIVE work, not an installation mandate.

**Provenance:** WQB458 ZIP SHA-256 `dee391d3c5c7d94c1bbadcc23363ab58e35adf617c2f4350a963d6c418c1d227`. WQD166 adds `musicbrainz_lookup.py`, a fourth proposal tab and focused mocked-network/Tk tests. Existing original WQB458 ZIP and historical manifests are preserved.

---

# Kyocera PC Playlist Desk + Bridge v0.14 — cross-playlist PC file reuse

**Offline source-only candidate.** Same existing task WQ-20261030-012; extends WQB449 v0.13, preserves original ZIP. No owner Windows, phone, audio file, ADB or deployment tested.

When a PC audio file was staged into playlist A, selecting the same file for playlist B used to skip it because the duplicate check was global. v0.14 reuses the existing editor-only track ID in B, without duplicating the inventory record. Choosing the file again within B is still skipped. Removing a reference from A keeps the PC-only record while B still references it; removing its last reference prunes that editor-only record. No file is opened, copied or transferred. Pending PC-only entries still prevent phone bridge planning/export until explicitly mapped by a future owner-approved workflow.

**Test on fictional data only:** run `launch_windows.cmd`, load `sample/fictional_phone_snapshot.json`, create two playlists, stage the same fictitious path in each using a mocked chooser/test harness; a real Windows file chooser requires actual file selection, which has not been exercised here. Unit and Linux Tk tests cover this behavior without accessing media.

---

# Kyocera PC Playlist Desk + Bridge v0.13 — held-pointer selection isolation

**Current WQB449 offline source-only candidate, 2026-10-31.** Existing shared task `WQ-20261030-012`; source copied from WQB448 v0.12, parent ZIP SHA-256 `27ddecfb05ca778c530edb3cfc8587b22b6484b9c0b14b5746a16e397b43eac7`. The parent archive and its source manifest are preserved. Windows 10 is the intended trial platform; only Linux/Tk synthetic tests were run here.

## Narrow v0.13 correction

Tk's built-in Listbox class receives `<B1-Motion>` when the app's own handler returns without `break` after a Shift/Ctrl click. In a reproducible Linux/Tk fixture, a Shift-click selected rows 1–4, but moving the held pointer to row 9 expanded the selection to 1–9 **without another click**. The app now suppresses that class-level motion in both Library and Playlist panes, while retaining the existing Shift-click range, Ctrl-click toggle, wheel scrolling, plain-click selection, group drag/drop, insertion marker, typed playlist buttons and Dumbplayer palette. The synthetic reproduction is related to the owner's report of selection changing while scrolling, but **does not prove its Windows root cause**.

**Interaction tradeoff:** holding Shift and dragging the mouse to paint a range no longer extends the selection. Shift-clicking the desired endpoint remains available; the owner explicitly reported Shift multi-select working. No metadata schema, file I/O, audio, phone, ADB, Gemma, MusicBrainz, or saved-playlist logic changed.

Use `launch_windows.cmd` with the included **fictional** `sample/fictional_phone_snapshot.json` on a disposable Windows 10 folder outside F:. See the accompanying WQB449 guide. This is not an installed or accepted release.

---

## Historical v0.12 and earlier documentation (retained for provenance)

# Kyocera PC Playlist Desk + Bridge v0.12 — safe M3U dot-segment matching

**Offline, source-only incremental candidate.** Existing shared queue item `WQ-20261030-012`, session WQB448. This extends WQB447 v0.11; the original ZIP, README and manifest are preserved. Python 3.9+ with Tkinter; Windows 10 is the target, **not yet physically tested**. No phone importer, ADB round-trip, actual audio transfer or deployment is claimed.

## New functionality

The existing **Review local playlist matches** dialog now accepts user-provided `.m3u` and `.m3u8` text files, as well as pasted `#EXTM3U` / `#EXTINF` lists. It retains the prior CSV/TXT, artist/album filter, and opt-in localhost Gemma tabs. No website URL is fetched, and imported media paths are **never opened, copied or played**. The imported text is a source for metadata matching only.

- Exact relative path match to the already loaded metadata can select a real local ID. Paths with `./` prefixes or backslashes are compared as text, never resolved on disk.
- When no exact path matches, an `#EXTINF` `Artist - Title` label can match local metadata. Duplicate editions stay **AMBIGUOUS** and require owner selection.
- Filename-only candidates are marked **REVIEW** even if unique, requiring explicit selection with **Use this ID**. If an exact path conflicts with `#EXTINF` artist/title, the row also requires manual review.
- Missing songs remain **MISSING**; no IDs are invented. The order of M3U entries is preserved, duplicate IDs are skipped with counts. Preview, Apply confirmation, Undo and separate Save As remain in force.
- The UI permits a bounded local file (100 KB / 100,000 characters, up to 1,000 entries). The file selection retains the existing protected-drive guard. File format detection uses `.m3u` / `.m3u8` for imported files and `#EXTM3U` / `#EXTINF` for pasted text. When replacing imported M3U text with pasted CSV, Auto detects the new content instead of retaining the stale file-extension hint. Use the visible format selector to override when needed.

## Disposable Windows 10 trial using only fictional data

1. Extract to a temporary folder **not on F:** and run `launch_windows.cmd`. Load `sample/fictional_phone_snapshot.json` (the same fictional sample as v0.9), create a **New Music** playlist named `M3U trial` and select it.
2. Open **Review local playlist matches**, select **Rebuild pasted playlist**, click **Open CSV/TXT/M3U/M3U8**, and choose `sample/fictional_external_playlist.m3u8`. Click **Preview local list**. Expect two MATCH rows (Álpha, Beta) and one MISSING row, with the intended order. The `https://example.invalid` entry is not fetched.
3. Confirm **Append reviewed matches**, check two local IDs added in order, then Undo. For a filename-only path such as `Chapter01.mp3`, expect REVIEW with an actual candidate but no auto-selection; choose **Use this ID** if appropriate. Do not test with real owner media or phone imports yet.

## Provenance and test boundaries

Parent WQB445 ZIP SHA-256 `2b0161f14966c7ce6246d5ad5d63d2146ac557671a1e5e8965399c74ccd5e64c`. Unit tests and Linux Tk/Xvfb GUI smoke passed on fictional metadata, including inherited selection, artist/album matching, drag/drop and local Gemma synthetic-response tests. No Windows installation, real phone export, external website, actual Ollama model, audio files, F: access, or Android device was used. This is **not a final owner-accepted release**.

Low-priority MusicBrainz and local audio/mood enhancements remain **ACTIVE**, not held. The owner's Windows v0.6 trial is the latest confirmed physical PC behavior, not proof this v0.11 candidate is installed.


## v0.11 list-format handling (WQB447)

The Rebuild pasted playlist tab now has an **Interpret list as** control. **Auto detect** recognizes `#EXTM3U` / `#EXTINF` content and treats an unedited local `.m3u` / `.m3u8` import as M3U, including headerless path-only lists. If you replace or edit imported text, the extension hint no longer overrides the new content. Choose **M3U/M3U8** explicitly when editing a headerless path-only M3U list; choose **Artist/title or CSV** for ordinary lists. The program never opens media paths or fetches URLs.

## v0.12 narrow correction (WQB448)

M3U path-only lists that contain harmless internal `./` components, such as `Music/./Album/song.mp3`, now compare as the same **text path** as `Music/Album/song.mp3`. This corrects a reproducible v0.11 mismatch where the former required manual filename review. It does not open, resolve or copy the referenced media. Parent `..` traversal, absolute paths and URLs are still excluded from automatic exact-path matching; any filename-only candidate requires manual review. The owner's actual Windows v0.6 trial remains the latest physical PC evidence.
