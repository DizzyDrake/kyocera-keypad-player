# Kyocera Playlist Desk + Bridge v0.7 — offline Windows source trial (WQB443)

This is a **sequential continuation of existing queue item `WQ-20261030-012`**, from WQD138 v0.6. Parent ZIP remains unchanged. It is a source candidate, **not an installed Windows release or an Android phone importer**.

## New in v0.7

- A separate **Find by artist / album or rebuild a pasted playlist** control in the *same integrated PC app*.
- **Exact artist and/or album** metadata filtering produces a reviewable list of concrete local track IDs. It retains the library's existing order, which is **not guaranteed album/chapter order**; reorder manually afterward if desired.
- **Outside playlist reconstruction:** paste `Artist - Title`, `Artist — Title`, `Artist | Title | Album`, or CSV with `artist,title[,album]` columns, or explicitly open a small local `.csv`/`.txt` export. No website URLs are fetched. Entries are matched to the *loaded local metadata only* and preserve input order.
- **Missing tracks and ambiguous editions** are shown rather than silently guessed. Choose a real candidate ID for an ambiguous row, or leave it unresolved. The Apply confirmation states the counts of skipped missing/unresolved/duplicate rows. A repeated ID is not inserted twice because the provisional phone bridge rejects duplicate playlist entries.
- **Review-first application:** the owner explicitly confirms appending resolved IDs to the currently selected Music or Audiobook playlist. Existing entries are preserved. This edits only the in-memory PC workspace, supports **Undo**, and still requires separate **Save As**. No phone sync, audio transfer, online lookup or model call.
- Parent v0.6's two-pane mouse selection fix, group drag, typed audiobook creation, offline plan/simulation and F: exclusions are retained.

## Disposable Windows 10 trial

1. Extract to a scratch folder **not on F:**. Python 3.9+ with Tkinter is required; run `launch_windows.cmd`. Load `sample/fictional_phone_snapshot.json` via **Load phone snapshot JSON…**.
2. Create a disposable **Music** playlist named `Outside sample`, select it, then choose **Find by artist / album or rebuild a pasted playlist…**. In the second tab open `sample/fictional_external_playlist.csv`, click **Preview pasted list**. Expect **2 MATCH / 1 MISSING** and the intended `Álpha`, `Beta` order.
3. Click **Append reviewed matches…** and confirm the explicit skip summary. The playlist should contain only those two tracks in order. Try **Undo last edit** to reverse the append. In the first tab, artist `Imaginary Group` and album `Example` should preview two existing IDs. Do not test on actual phone data until this disposable behavior is acceptable.

For a duplicate-edition trial, use fictional metadata containing two records with the same artist/title but different albums. A pasted `Artist - Title` row should say **AMBIGUOUS**, not select either automatically. Use `Artist | Title | Album` to narrow it or select a specific local candidate in the preview.

## Limits and provenance

- No Windows 10/owner installation or real export byte inspection in this session; Linux Xvfb/Tk tests are surrogate checks. The owner previously reported a real DEV8 JSON export loaded in the bridge, but that does not validate phone-side import or this new candidate.
- No Gemma/Ollama yet; optional local Gemma-assisted interpretation of messy lists remains a separate **active** follow-up. MusicBrainz and audio/mood analysis remain **active low priority**, not paused or cancelled.
- Pasted input: at most 100,000 characters / 1,000 entries. CSV/TXT file input: 100 KB cap, UTF-8. No M3U parsing, direct URL fetch, fuzzy title matching, audio inspection or silent track identity inference.
- Only the selected artist/album filters are exact (casefold and Unicode NFKC normalization). The bridge's phone plan remains provisional; the original phone snapshot and existing playlists are not overwritten by the new matcher. Playlist-to-library dragging still removes references only, pending owner confirmation.
- The sample contains entirely fictional titles/artists and no private music library data.
