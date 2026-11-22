# Kyocera Playlist Desk — Gemma 4 artist-first correction (November 8, 2026)

**Status: new offline SOURCE CANDIDATE for Windows trial. Not an installed/accepted release.**
**Parent:** unchanged WQB164 integrated source ZIP (`da0f8621ae43ae2768f37e17f28ea06b01466f6baa41f929205511d7fd8caeb3`). This is a direct continuation of the existing PC Playlist Desk / Bridge project; saved-plan reopening, NOT filtering, CSV/M3U, existing offline matching, optional MusicBrainz, and other inherited functions are retained.

## Owner observation motivating correction

On her Windows PC with `gemma4:12b`, the owner requested Jimi Hendrix. Earlier Gemma responses had the wrong JSON shape (`{"596": ["Charming Disaster", "Super Natural History"], ...}`). With structured JSON output enabled, Gemma returned many catalog indices concentrated at 486–595 and Playlist Desk expanded these into **461 unrelated tracks**. These are owner observations of the pre-correction application, not observations of the new candidate.

## This candidate changes

- **Exact local artist-first path.** Enter `Jimi Hendrix`, `find Jimi Hendrix`, or `songs by Jimi Hendrix` in **Optional local Gemma** and click **Preview local artist / ask Gemma…**. If the loaded library has an exact normalized artist credit, the preview contains only those locally verified artist tracks. **Ollama is not called.** Comparison is case-insensitive; a leading `The` is tolerated. A different artist name (e.g., a tribute band) is not silently treated as the same artist.
- **Missing explicit artist stops locally.** An explicit `songs by <artist>` with no matching local metadata returns an explanatory error and cannot fall through to model guessing. Check the artist's actual metadata credit or use the ordinary manual filter.
- **Narrowed model catalog where justified.** For more complex requests explicitly mentioning catalog artist names or distinctive albums, sends only the matching pair subset to Gemma. Open-ended/similarity/negative prompts retain the bounded full catalog; the program does not guess a semantic subset.
- **Conservative model-result guard.** A model proposal exceeding **20 catalog artist/album pairs or 120 expanded tracks** is rejected instead of being actionable. This applies to uncertain *model* suggestions; deterministic exact artist results retain the existing 2,000-row technical bound. Smaller model suggestions remain unverified and require deliberate review before Apply. These are candidate safety thresholds, not permanent owner restrictions.
- **Gemma 4 config.** Default editable model name `gemma4:12b`; local Ollama request sends `think: false` and JSON Schema requiring `{ "indices": [1, 2] }`-style integer output. Older manually entered installed model names still work if supported by Ollama.
- **Previews cannot be reused after a failed new request.** Beginning another Gemma preview clears the previous preview, avoiding accidental Apply from an earlier request. Existing source-signature/selected-playlist stale guard, explicit Apply, Undo, and separate Save As remain.
- **Optional response diagnostic.** Launch PowerShell in this source folder; to log raw Gemma responses in that terminal for that session, run `$env:PLAYLIST_DESK_DEBUG_GEMMA='1'` before `py -3 integrated_app.py`. Debugging is OFF by default (responses may contain artist/album strings).

## Disposable Windows trial

1. Extract the ZIP to a **new working directory**, outside your existing installation and outside protected drives, preserving your current installed Playlist Desk. Run `launch_windows.cmd` (or `py -3 integrated_app.py`). Python 3.9+ with Tkinter is required. No installs or phone transfers occur automatically.
2. First load the fictional `sample/fictional_phone_snapshot.json`, select/create a Music playlist, open **Review local playlist matches → Optional local Gemma**, enter `Imaginary Group`, and click **Preview local artist / ask Gemma…**. Expect the two fictional tracks Beta and Álpha (accent in title: `Álpha`), and a message saying **Ollama was not contacted**. Nothing is saved or added.
3. In the same dialog try `songs by Nobody Exists`: expect a local error, with the prior preview cleared. For actual model testing, enter a more complex ambiguous query, confirm `gemma4:12b` is installed and Ollama running, and click the same button. The model still only produces *proposals*; do not Apply incorrect tracks. Huge proposals should be rejected with a count; manually inspect smaller suggestions.
4. Once fictional behavior is satisfactory, you may choose your own real-library test. For `Jimi Hendrix`, inspect which **artist credit** is actually present in the metadata. An artist credited only as `The Jimi Hendrix Experience` is a distinct exact credit and will not be silently merged with `Jimi Hendrix`.

## Verification and limits

- 216/216 Python unit tests PASS, including 12 newly added regression tests for artist-first lookup, Gemma4 request schema, model overselction and source isolation.
- 15/16 GUI scripts PASS using real Tk8.6 under Linux Xvfb. The one failure, `tests/gui_smoke.py` (status string `edits retained`), also occurs on the untouched WQB164 source ZIP and is **preexisting**. No claim of complete GUI parity.
- `tests/gui_artist_first_guard.py` PASS: exact local artist previews bypass Ollama, missing-artist failure clears rows, ambiguous prompt invokes mocked opt-in request. Inherited `tests/gui_wqb445.py` PASS.
- No actual Ollama/Gemma4 model response was contacted during these synthetic tests; no Windows native UI, owner music metadata, installed app, USB/ADB, phone, audio bytes, or production import were tested.
- Parent WQB164 ZIP/source unchanged. Older embedded historical SHA manifests refer to previous candidates and are not assertions about this candidate; use the separate new `CURRENT_GEMMA_ARTIST_FIRST_MANIFEST_20261108.json` for candidate hashes.

## Source / diagnostics

Changed `gemma_local.py`, `proposal_ui.py`; added `tests/test_artist_first_guard.py`, `tests/gui_artist_first_guard.py`, this README, fresh manifest, and an exact unified diff patch. All other Python application source files are preserved byte-for-byte from WQB164. This archive contains source, fixtures, tests, launch scripts, and no executable installer/APK. Nothing was modified on the owner's PC.
