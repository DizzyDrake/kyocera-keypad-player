# Kyocera PC Playlist Desk + Bridge v0.8 — offline Windows source trial (WQD139)

This is a **sequential continuation of existing queue item `WQ-20261030-012`** from WQB443 v0.7. Its original Library ZIP is preserved and SHA-256 checked. This package is an **owner-testable source candidate**, not a final release, an Android importer, or an installed Windows update.

## v0.8 changes, from the owner's actual v0.6 Windows feedback

- **Visible insertion line:** while dragging from Library to Playlist or reordering within Playlist, a burgundy 3-pixel line previews the destination row boundary. The preview does not mutate playlist contents; the line disappears on release. Library-to-Library reordering remains intentionally unsupported.
- **Separate playlist buttons:** **New Music** and **New Audiobook** replace the shared type-choice dialog. A name prompt remains. Music/Audiobook metadata and manual chapter order are retained.
- **Dumbplayer colors:** desktop header `#713E46`, main background `#F5F0EB`, soft controls `#E9DCD8`, selected rows `#D6A6AD`, text `#252022`. These came from the DEV8 app source and are not the RoarinCreations palette.
- **Scroll/selection correction:** block Tk Listbox's `B1-Leave` automatic repeat scrolling, cancel pending repeats on mouse release or wheel scroll, and restore the Library pane's prior horizontal offset after an unsupported internal drag. Explicit Ctrl toggles, Shift ranges, group dragging, wheel scrolling and scrollbar scrolling remain supported.
- All v0.7 **artist/album filtering and pasted/CSV/TXT external playlist matching** remain in this integrated app, with preview, missing/ambiguous review, owner confirmation, Undo and separate Save As. No new network/model calls.

## Bounded Windows 10 trial (fictional data first)

1. Extract the source ZIP into a **disposable local folder outside F:**. Keep the files together. Python 3.9+ with Tkinter is required. Double-click `launch_windows.cmd` or run `py -3 integrated_app.py`. Use **Load phone snapshot JSON…** and select `sample/fictional_phone_snapshot.json`.
2. Test **New Music** and **New Audiobook**; each should ask only for a name, then show the selected type at the top right. Use Shift and Ctrl to select several Library rows, drag into the Playlist, and watch for the thin burgundy insertion line. Drag within Playlist to reorder; release outside the lists to cancel.
3. Select one row, release the mouse, then use the mouse wheel and the scrollbar in both panes. Selection should **not** grow into a range. Try dragging within Library (unsupported): it should **not** drift sideways. Test the v0.7 artist/album and pasted playlist matching using `sample/fictional_external_playlist.csv`; confirm Undo still works.

**What to report:** whether the insertion line appears and follows the intended boundary; whether both creation buttons and colors are comfortable; whether either unintended sideways scroll or selection-growth bug remains (and exactly what pointer/wheel/scrollbar sequence reproduces it); whether cross-pane group drag still works. Preserve the state and describe what happened before restarting if an unusual bug appears.

## Source, tests and limits

- Original v0.7 parent ZIP SHA-256: `8fd3db82c016603b75741db555fe5f0c1ff83ca3ef5538321553b39f6b45fe3b`. Historical README preserved as `README_WQB443_PARENT.md`.
- Offline test set: 122 Python unit tests and seven Linux/Xvfb Tk scripts, including new v0.8 scroll/indicator/button checks. The old v0.6 GUI script was updated in this **new** candidate only because its old expectation of a type-choice dialog is intentionally superseded; the original test is preserved in the unmodified v0.7 parent ZIP.
- The source-only fixes were not exercised on the owner's Windows 10 computer, with her actual mouse/scrollbar or private metadata. Tk's autoscan binding is directly observable in Linux Tk; whether it caused **every** Windows symptom remains unverified.
- **No phone write/import/ADB**, no actual media transfer, no local Gemma/Ollama, no MusicBrainz or audio/mood analysis. Those optional features remain **active** at their respective priorities, not on hold. No original audio or metadata was modified. The existing bridge plan remains provisional.
- The preview insertion cue does not alter actual insertion semantics; unsupported playlist-to-library reference removal remains provisional pending owner confirmation.
