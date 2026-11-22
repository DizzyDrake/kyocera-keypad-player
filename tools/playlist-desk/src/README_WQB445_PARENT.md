# Kyocera PC Playlist Desk + Bridge v0.9 — optional local Gemma proposals

**Offline source candidate, not an installed Windows release.** Sequential continuation of WQD139 v0.8, existing queue item `WQ-20261030-012`. The previous v0.8 source ZIP is unchanged and retained in the Library. Python 3.9+ and Tkinter required. No phone importer, ADB sync, live media transfer or deployment.

## New in v0.9

The existing **Find by artist / album or rebuild a pasted playlist** window has an **Optional local Gemma** tab. Enter an artist/album request and an already-installed Ollama model name (the default `gemma3:4b` is an editable example, not a claim it is installed). Clicking **Ask local Gemma** sends **only distinct artist/album strings and the typed request** to a fixed `http://127.0.0.1:11434/api/generate` endpoint. No track titles, file paths, IDs, audio bytes or full phone JSON are included in the prompt. This request is **opt-in**; merely opening the app never calls Ollama. The app itself makes no external web requests; behavior of a separately configured local Ollama service is outside this test.

Gemma can return only **catalog positions**, never authoritative track IDs. The app rejects invalid positions, maps accepted positions back to the actual loaded local track IDs, shows the proposed songs, and requires the same explicit **Append reviewed matches** confirmation as manual matching. The playlist remains in memory until separate Save As; Undo remains available. The response is discarded if the library or selected playlist changed while Gemma was thinking. Failure, missing model, oversize catalogs, timeout or invalid model output leave manual matching usable. The model request has a 90-second timeout; no model installation or download is attempted.

## Disposable Windows 10 trial (no owner files needed)

1. Extract ZIP to a disposable local directory **outside F:**. Launch `launch_windows.cmd` (or `py -3 integrated_app.py`); load `sample/fictional_phone_snapshot.json`, then select or create a Music playlist.
2. Open the matching dialog and try manual **Find by artist / album** and **Rebuild pasted playlist** first. These should work without Ollama. Then, **only if you already run local Ollama and have a Gemma model installed**, open Optional local Gemma, enter its exact installed model name, type `Find Imaginary Group's Example album`, and click the opt-in button. Expect two fictional tracks, `Beta` and `Álpha`, and no automatic playlist edit. Confirm Apply if desired, then Undo.
3. For unavailable Ollama/model, expect a clear error after the bounded request and continued manual matching. The local model may choose no pairs or wrong pairs; those are **proposals**, not ground truth. Report the actual rows shown, any invalid-choice count, and whether Apply/Undo behaved correctly. Do not use real metadata or phone import yet.

## Verification scope

- 141 Python unit tests PASS, including 19 new local Gemma boundary checks.
- Seven Linux/Xvfb Tk GUI scripts PASS, including a new opt-in/preview/stale-metadata script.
- Python compileall PASS. No real Ollama/Gemma response, Windows 10 trial, owner metadata, phone, ADB, physical device or web service tested.
- Original v0.8 owner UX changes, v0.7 matcher and old source files are preserved. Optional MusicBrainz and audio/mood work remain **low priority but active**, not paused.

**Privacy limitation:** The application sends selected metadata strings to a service bound to localhost; if that separate service is configured to relay or log them, this application cannot verify or control that. Use fictional data for first trials. No local model was contacted in the development environment.
