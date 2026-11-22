# Kyocera Playlist Desk + Metadata Bridge v0.3 — one-window offline trial

**Worker B WQ-20261030-012 / WQB434 · 2026-10-30.** Windows 10-targeted Python 3.9+ **source candidate**, not an installer. This is a feature integration of the existing **WQ140 Playlist Desk v0.2** and **WQ146 Metadata Bridge v0.1.1**, not a replacement for either frozen package. It contains **no ADB calls, no phone import, no audio-file operations, no network access**. It can edit only JSON that you explicitly open and write only to an explicitly selected destination. Start with the fictional samples; do not select actual personal music metadata, real media, or protected drives for the initial trial.

## What is new

One Tkinter window now offers all three operations without switching applications or saving an intermediate editor JSON:

1. **Load fictional phone snapshot** — reads a *provisional-schema* JSON snapshot and immediately populates the familiar Playlist Desk library and manual-order editor. You can reorder, rename, add, remove, create and save playlists with the original WQ140 controls.
2. **Save proposed changes…** — generates a new **offline plan JSON** from the exact snapshot and current unsaved editor order, with unchanged/new/updated playlists distinguished. It does not change the snapshot or any phone.
3. **Save simulated result…** — generates a separate **fictional next-revision snapshot JSON**, preserving audiobook bookmarks and listening positions. It is **not a phone import file**. Both bridge actions require NEW filenames and refuse overwrites.

If you reopen a saved editor JSON, then load its **exact matching** phone snapshot, the app retains your edited playlist order. A mismatched snapshot prompts before discarding unsaved edits; the bridge rejects stale or altered snapshot/track identities. Opening another editor JSON detaches the previously selected phone snapshot until explicitly reattached.

## Windows 10 fictional trial

Extract this ZIP into a fresh ordinary folder on your Windows computer. Python 3.9+ with Tkinter is required; **no extra pip packages**. Double-click `launch_windows.cmd` (or run `py -3 integrated_app.py`). If Python is missing or Tkinter is not installed, the app will not open; there is no compiled EXE.

1. Click **Load fictional phone snapshot**, choose `sample/fictional_phone_snapshot.json`. You should see three fictional tracks and playlists **My order** and **Story**. You may alternatively try `sample/dev8_fictional_phone_export.json`, which came from DEV8 **source**, not a real phone.
2. Choose **My order**, highlight its first track, click **↓ Move down**. The playlist should now display Álpha before Beta (the title is **Álpha**, without a space). Click **Save proposed changes…**, select a NEW `test_plan.json` in a disposable folder. A plan is created; nothing is transferred.
3. Click **Save simulated result…**, select a NEW `test_simulated.json`. The fictional revision increases from 7 to 8, the manual playlist order is preserved, and music/audiobook positions and bookmarks remain unchanged. Optionally **Save As JSON** to a NEW editor file, reopen it, then reload the matching snapshot to retain the order.

Use Tab, arrows and Enter for ordinary Tkinter navigation. `Ctrl+O` opens PC editor JSON; `Ctrl+Shift+S` saves a new PC editor JSON. The output files are separate from the original snapshot. A deliberately repeated output filename is refused for bridge results.

**Rollback:** close the window and delete only the extracted trial folder and your new fictional outputs. No registry entries, audio files or phone content are changed by the app.

## Exact status and interoperability boundary

- The **DEV8 v0.2.2 source ZIP** contains `PhoneSnapshotExport.java` and a fictional JSON sample using the same `kyocera-phone-snapshot-v0.1-PROVISIONAL` contract. This is **source-level compatibility**, not proof that the owner's installed DEV4 export bytes use that contract or that DEV8 is installed. The owner reported a metadata export and manual retrieval on an earlier phone build, but its exact bytes/schema have not been inspected here.
- WQ146's phone snapshot contract is still **provisional**. The owner cannot currently send these plan/simulation files back into the installed player as a verified import. Actual Android importer, owner-controlled ADB transfer, track identity persistence, Windows 10 runtime, NTFS and phone acceptance remain unverified.
- Phone snapshot JSON may contain private filenames. Keep real exports local and avoid uploading them for support; sanitized counts and schema keys are enough for first diagnosis.
- WQ140's output guard blocks direct `F:` and Windows device paths, but junction/alias protections are incomplete. Use only an ordinary disposable folder for trials. No tool in this package needs access to `F:`.
- New PC playlists do not cause implicit deletion of existing phone playlists. The bridge refuses edits removing a currently playing track; it preserves bookmarks and listening progress.

## Source provenance and tests

- WQ140 Desk v0.2 original ZIP SHA-256: `493f2ab74d4aa94a59d2e2d471639792062803a704f2cb9702aedc72ae708d3f`.
- WQ146 Bridge v0.1.1 original ZIP SHA-256: `34652c3a3d39a643a070e460b8c04ece41b171c1754f719418469937528b2640`.
- DEV8 source-only ZIP SHA-256: `db04dc97e79aefc430d44acbee53815a8c4365b65413386d4bb1015dd9e9e582` (source of fictional sample only).
- `app.py`, `playlist_core.py` are unmodified WQ140 copies; `bridge.py` is an unmodified WQ146 copy. `integrated_app.py` and `integration_core.py` are the new integration. `SOURCE_MANIFEST.json` lists member hashes.

Offline verification in Linux Python 3.13: **82/82** inherited/new unittest cases pass, `compileall` passes, and an Xvfb Tk GUI smoke test passes (import → reorder → plan → simulate → no-clobber → save/reopen/reattach). To rerun the portable tests: `py -3 -m unittest discover -s tests -v`. `tests/gui_smoke.py` requires a GUI display and uses a synthetic test harness; it is not required for a normal trial. **No Windows 10, Android, ADB, or physical device was tested by Worker B.**
