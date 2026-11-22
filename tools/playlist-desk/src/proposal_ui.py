"""Review-first local metadata playlist matching UI for the integrated PC bridge."""
import hashlib
import json
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from gemma_local import (catalog_pairs, plan_artist_first, checked_model_rows,
                         request_local_model, rows_from_indices)
from musicbrainz_lookup import MusicBrainzError, build_query, lookup_recordings, _contact
from playlist_core import validate_output
from playlist_match import (MatchError, filter_artist_album, match_entries,
                            parse_pasted, parse_m3u, match_m3u, choose_list_format, resolved_ids)
from two_pane_actions import insert_selected


def _signature(tracks):
    return hashlib.sha256(json.dumps(tracks, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


class ProposalDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title('Review local playlist matches — PC workspace')
        self.geometry('910x670')
        self.minsize(740, 500)
        self.rows = []
        self.snapshot_signature = None
        self.playlist_name = None
        self.lookup = {}
        self.mode = None
        self.transient(app)
        self.protocol('WM_DELETE_WINDOW', self.destroy)

        ttk.Label(self, text='Manual matching is offline. Optional Gemma sends artist/album names to local Ollama only when clicked. Nothing is sent to the phone.',
                  wraplength=840).pack(fill='x', padx=12, pady=(12, 6))
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill='x', padx=12)
        artist_tab, pasted_tab, gemma_tab, mb_tab = (ttk.Frame(self.tabs) for _ in range(4))
        self.tabs.add(artist_tab, text='Find by artist / album')
        self.tabs.add(pasted_tab, text='Rebuild pasted playlist')
        self.tabs.add(gemma_tab, text='Optional local Gemma')
        self.tabs.add(mb_tab, text='MusicBrainz (optional)')
        self.artist = tk.StringVar()
        self.album = tk.StringVar()
        for i, (label, variable) in enumerate((('Exact artist:', self.artist), ('Exact album:', self.album))):
            ttk.Label(artist_tab, text=label).grid(row=i, column=0, sticky='w', padx=6, pady=5)
            ttk.Entry(artist_tab, textvariable=variable).grid(row=i, column=1, sticky='ew', padx=6, pady=5)
        artist_tab.columnconfigure(1, weight=1)
        ttk.Button(artist_tab, text='Preview matching local tracks', command=self.preview_artist).grid(
            row=2, column=0, columnspan=2, sticky='w', padx=6, pady=5)
        ttk.Label(pasted_tab, text='Paste Artist - Title / Artist | Title | Album, CSV, or #EXTM3U / #EXTINF list. Import local .m3u/.m3u8 without opening any media or URLs.',
                  wraplength=830).pack(anchor='w', padx=6, pady=4)
        self.pasted_format_hint = None  # File extension hint only for unchanged imported text.
        self.pasted_import_signature = None
        self.list_format = tk.StringVar(value='Auto detect')
        self.pasted = tk.Text(pasted_tab, height=5, wrap='none')
        self.pasted.pack(fill='x', padx=6, pady=3)
        format_bar = ttk.Frame(pasted_tab)
        format_bar.pack(fill='x', padx=6)
        ttk.Label(format_bar, text='Interpret list as:').pack(side='left')
        ttk.Combobox(format_bar, textvariable=self.list_format, state='readonly', width=23,
                     values=('Auto detect', 'Artist/title or CSV', 'M3U/M3U8')).pack(side='left', padx=6)
        ttk.Label(format_bar, text='Auto uses file extension only while imported text is unchanged.').pack(side='left')
        ttk.Button(pasted_tab, text='Open CSV/TXT/M3U/M3U8…', command=self.load_pasted_file).pack(
            side='left', padx=6, pady=5)
        ttk.Button(pasted_tab, text='Preview local list (no media/URL fetch)', command=self.preview_pasted).pack(
            side='left', padx=6, pady=5)
        ttk.Label(gemma_tab, text='Opt-in: sends ONLY distinct artist/album names and your request to Ollama on this PC (127.0.0.1:11434). No titles, paths, IDs, files, phone writes or external web calls.',
                  wraplength=820).pack(anchor='w', padx=6, pady=4)
        modelbar = ttk.Frame(gemma_tab)
        modelbar.pack(fill='x', padx=6)
        ttk.Label(modelbar, text='Installed Ollama model:').pack(side='left')
        self.model_name = tk.StringVar(value='gemma4:12b')
        ttk.Entry(modelbar, textvariable=self.model_name, width=24).pack(side='left', padx=6)
        ttk.Label(gemma_tab, text='Enter an artist for exact local matching, or a request for Gemma (review its suggestions before Apply):').pack(anchor='w', padx=6)
        self.gemma_request = tk.Text(gemma_tab, height=3, wrap='word')
        self.gemma_request.pack(fill='x', padx=6, pady=3)
        self.gemma_button = ttk.Button(gemma_tab, text='Preview local artist / ask Gemma…', command=self.preview_gemma)
        self.gemma_button.pack(anchor='w', padx=6, pady=4)
        self._gemma_queue = None
        ttk.Label(mb_tab, text='Optional internet lookup. Only the artist/title you type and the contact URL/email below are sent to MusicBrainz when you click Search. Your library, paths, track IDs and phone data are never uploaded.',
                  wraplength=820).pack(anchor='w', padx=6, pady=4)
        mb_fields = ttk.Frame(mb_tab)
        mb_fields.pack(fill='x', padx=6)
        self.mb_artist = tk.StringVar()
        self.mb_title = tk.StringVar()
        for i, (label, variable) in enumerate((('Artist:', self.mb_artist), ('Recording title:', self.mb_title))):
            ttk.Label(mb_fields, text=label).grid(row=i, column=0, sticky='w', padx=4, pady=2)
            ttk.Entry(mb_fields, textvariable=variable).grid(row=i, column=1, sticky='ew', padx=4, pady=2)
        self.mb_contact = tk.StringVar()
        ttk.Label(mb_fields, text='Contact URL/email:').grid(row=2, column=0, sticky='w', padx=4, pady=2)
        ttk.Entry(mb_fields, textvariable=self.mb_contact).grid(row=2, column=1, sticky='ew', padx=4, pady=2)
        ttk.Label(mb_tab, text='MusicBrainz requires a maintainer contact in the User-Agent. It is sent only when you click Search, and is not saved by this app.', wraplength=820).pack(anchor='w', padx=6, pady=2)
        mb_fields.columnconfigure(1, weight=1)
        self.mb_button = ttk.Button(mb_tab, text='Search MusicBrainz (internet)…', command=self.preview_musicbrainz)
        self.mb_button.pack(anchor='w', padx=6, pady=4)
        self.mb_results = []
        self.mb_list = tk.Listbox(mb_tab, height=4, exportselection=False)
        self.mb_list.pack(fill='x', padx=6, pady=3)
        ttk.Button(mb_tab, text='Compare selected recording with local tracks',
                   command=self.compare_musicbrainz).pack(anchor='w', padx=6, pady=4)
        self._mb_queue = None
        self.summary = tk.StringVar(value='Preview a filter or paste a list. Nothing changes until you confirm Apply.')
        ttk.Label(self, textvariable=self.summary, wraplength=850).pack(fill='x', padx=12, pady=(8, 3))
        listing = ttk.Frame(self)
        listing.pack(fill='both', expand=True, padx=12, pady=5)
        listing.rowconfigure(0, weight=1)
        listing.columnconfigure(0, weight=1)
        self.preview = tk.Listbox(listing, exportselection=False, font=('Segoe UI', 10))
        self.preview.grid(row=0, column=0, sticky='nsew')
        self.preview.bind('<<ListboxSelect>>', self.show_choices)
        scrollbar = ttk.Scrollbar(listing, command=self.preview.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.preview.configure(yscrollcommand=scrollbar.set)
        controls = ttk.Frame(self)
        controls.pack(fill='x', padx=12, pady=4)
        ttk.Label(controls, text='Selected row candidate:').pack(side='left')
        self.candidate = ttk.Combobox(controls, state='readonly', width=64)
        self.candidate.pack(side='left', fill='x', expand=True, padx=6)
        ttk.Button(controls, text='Use this ID', command=self.resolve).pack(side='left', padx=5)
        actions = ttk.Frame(self)
        actions.pack(fill='x', padx=12, pady=(6, 12))
        ttk.Button(actions, text='Append reviewed matches to current playlist…', command=self.apply).pack(side='left')
        ttk.Button(actions, text='Close', command=self.destroy).pack(side='right')
        self.grab_set()

    def _tracks(self):
        if self.app.data is None:
            raise MatchError('Load metadata before matching.')
        return self.app.data['tracks']

    def _set_rows(self, rows, mode):
        self.rows = rows
        self.mode = mode
        self.snapshot_signature = _signature(self._tracks())
        self.playlist_name = self.app.selector.get()
        self.lookup = {t['id']: t for t in self._tracks()}
        self.preview.delete(0, tk.END)
        self.candidate.set('')
        self.candidate['values'] = ()
        for i, row in enumerate(rows, 1):
            e = row['entry']
            name = f"{e.get('artist', '')} — {e.get('title', '')}" if e.get('title') else e.get('path', '(untitled)')
            if e.get('album'):
                name += f" [{e['album']}]"
            self.preview.insert('end', f"{i:>3}. {row['status']:<10} {name}" +
                                (f"  ({row['match_basis']})" if row.get('match_basis') else ''))
        counts = {s: sum(r['status'] == s for r in rows) for s in ('MATCH', 'AMBIGUOUS', 'MISSING', 'REVIEW')}
        self.summary.set(f"{len(rows)} entries: {counts['MATCH']} exact; {counts['AMBIGUOUS']} ambiguous; "
                         f"{counts['MISSING']} missing; {counts['REVIEW']} filename-only review. Order retained. "
                         f"Preview for playlist: {self.playlist_name or 'none'}.")

    def preview_artist(self):
        try:
            matches = filter_artist_album(self._tracks(), self.artist.get(), self.album.get())
            # A filter acts on concrete local metadata records, not guessed
            # title/artist matches; keep each exact ID even for duplicate titles.
            rows = [{'entry': {'artist': t.get('artist', ''),
                               'title': t.get('title') or t.get('path', '(untitled)'),
                               'album': t.get('album', ''), 'source': 'local metadata'},
                     'candidate_ids': [t['id']], 'chosen_id': t['id'], 'status': 'MATCH'}
                    for t in matches]
            self._set_rows(rows, 'artist')
        except MatchError as exc:
            messagebox.showerror('Cannot preview', str(exc), parent=self)

    def load_pasted_file(self):
        path = filedialog.askopenfilename(parent=self, title='Open a local track-list export',
                                          filetypes=[('Track lists CSV/TXT/M3U/M3U8', '*.csv *.txt *.m3u *.m3u8'),
                                                     ('All files', '*.*')])
        if not path:
            return
        try:
            target = validate_output(path)  # F: remains excluded, even for read-only input
            if target.stat().st_size > 100_000:
                raise MatchError('Export exceeds 100 KB; use a smaller track list.')
            content = target.read_text(encoding='utf-8-sig')
            if len(content) > 100_000:
                raise MatchError('Export exceeds 100,000 characters.')
            self.pasted.delete('1.0', 'end')
            self.pasted.insert('1.0', content)
            self.pasted_format_hint = 'm3u' if target.suffix.lower() in ('.m3u', '.m3u8') else None
            self.pasted_import_signature = hashlib.sha256(content.encode('utf-8')).hexdigest()
            self.list_format.set('Auto detect')
            self.tabs.select(1)
            self.summary.set('Local list loaded for review. No media or URLs opened. Click Preview local list.')
        except (OSError, UnicodeError, ValueError) as exc:
            messagebox.showerror('Cannot open list', str(exc), parent=self)

    def preview_pasted(self):
        try:
            content = self.pasted.get('1.0', 'end-1c')
            same_as_import = (self.pasted_import_signature is not None and
                              hashlib.sha256(content.encode('utf-8')).hexdigest() == self.pasted_import_signature)
            hint = self.pasted_format_hint if same_as_import else None
            fmt = choose_list_format(content, self.list_format.get(), hint)
            if fmt == 'm3u':
                entries = parse_m3u(content)
                self._set_rows(match_m3u(entries, self._tracks()), 'm3u')
            else:
                entries = parse_pasted(content)
                self._set_rows(match_entries(entries, self._tracks()), 'pasted')
        except MatchError as exc:
            messagebox.showerror('Cannot preview', str(exc), parent=self)

    def preview_gemma(self):
        if self._gemma_queue is not None:
            return
        # A failed or pending new search must not leave an older model proposal
        # eligible for Apply under the guise of the latest request.
        self.rows = []
        self.mode = None
        self.snapshot_signature = None
        self.preview.delete(0, tk.END)
        try:
            tracks = self._tracks()
            request = self.gemma_request.get('1.0', 'end-1c')
            pairs, local, scope = plan_artist_first(request, catalog_pairs(tracks))
            # Exact artist identification is deterministic and local; do not
            # contact Ollama or require a model to be installed or running.
            if local:
                rows = rows_from_indices(tracks, pairs, list(range(1, len(pairs) + 1)))
                self._set_rows(rows, 'artist')
                self.summary.set(f'{len(rows)} tracks matched {scope} in local metadata. '
                                 'Ollama was not contacted. Review before Apply; nothing saved.')
                return
            model = self.model_name.get()
            from gemma_local import make_prompt
            make_prompt(request, pairs)  # Enforce prompt-size bounds BEFORE worker.
            if not model.strip():
                raise MatchError('Enter the name of an installed Ollama model.')
        except MatchError as exc:
            messagebox.showerror('Cannot preview local artist / request Gemma', str(exc), parent=self)
            return
        source_signature = _signature(tracks)
        source_playlist = self.app.selector.get()
        self._gemma_queue = queue.Queue(maxsize=1)
        self.gemma_button.configure(state='disabled')
        self.summary.set(f'Waiting for local Ollama response, using {len(pairs)} {scope} pair(s). '
                         'No playlist edits (up to 90 seconds).')
        q = self._gemma_queue
        def worker():
            try:
                q.put(('ok', request_local_model(request, pairs, model)))
            except Exception as exc:
                q.put(('error', f'{type(exc).__name__}: {exc}'))
        threading.Thread(target=worker, daemon=True).start()
        self.after(100, lambda: self._poll_gemma(q, pairs, source_signature, source_playlist))

    def _poll_gemma(self, q, pairs, source_signature, source_playlist):
        if not self.winfo_exists():
            return
        try:
            status, payload = q.get_nowait()
        except queue.Empty:
            self.after(100, lambda: self._poll_gemma(q, pairs, source_signature, source_playlist))
            return
        self._gemma_queue = None
        self.gemma_button.configure(state='normal')
        if status == 'error':
            self.summary.set('Local model unavailable or invalid. Manual artist/album and pasted matching remain available.')
            messagebox.showerror('Local Gemma proposal failed', payload, parent=self)
            return
        if self.app.data is None or _signature(self._tracks()) != source_signature or self.app.selector.get() != source_playlist:
            self.summary.set('Library or selected playlist changed while the local model was responding. Preview again.')
            return
        indices, invalid = payload
        try:
            rows = checked_model_rows(self._tracks(), pairs, indices)
            self._set_rows(rows, 'gemma')
            self.summary.set(f'Gemma suggested {len(indices)} catalog pair(s), yielding {len(rows)} actual local tracks; '
                             f'{invalid} invalid choices ignored. Model choices are unverified: review every row before Apply. No writes yet.')
        except MatchError as exc:
            self.rows = []
            self.preview.delete(0, tk.END)
            self.summary.set('Model proposal rejected as too broad. No rows available to Apply.')
            messagebox.showerror('Gemma proposal rejected', str(exc), parent=self)

    def preview_musicbrainz(self):
        if self._mb_queue is not None:
            return
        try:
            artist, title, contact = self.mb_artist.get(), self.mb_title.get(), self.mb_contact.get()
            build_query(artist, title)  # Reject invalid terms before network I/O.
            _contact(contact)
        except MusicBrainzError as exc:
            messagebox.showerror('Cannot search MusicBrainz', str(exc), parent=self)
            return
        self.mb_results = []
        self.mb_list.delete(0, 'end')
        self._mb_queue = queue.Queue(maxsize=1)
        self.mb_button.configure(state='disabled')
        self.summary.set('Contacting MusicBrainz with your typed artist/title and contact only. No local catalog sent.')
        q = self._mb_queue
        def worker():
            try:
                q.put(('ok', lookup_recordings(artist, title, contact)))
            except Exception as exc:
                q.put(('error', f'{type(exc).__name__}: {exc}'))
        threading.Thread(target=worker, daemon=True).start()
        self.after(100, lambda: self._poll_musicbrainz(q))

    def _poll_musicbrainz(self, q):
        if not self.winfo_exists():
            return
        try:
            status, payload = q.get_nowait()
        except queue.Empty:
            self.after(100, lambda: self._poll_musicbrainz(q))
            return
        self._mb_queue = None
        self.mb_button.configure(state='normal')
        if status == 'error':
            self.summary.set('MusicBrainz unavailable. Offline artist/album and pasted matching still work.')
            messagebox.showerror('MusicBrainz lookup failed', payload, parent=self)
            return
        self.mb_results = payload
        for row in payload:
            albums = ', '.join(row['albums']) if row['albums'] else 'release unspecified'
            self.mb_list.insert('end', f"{row['artist']} — {row['title']} [{albums}]  MBID {row['mbid']}")
        self.summary.set(f'{len(payload)} MusicBrainz recording candidate(s). Select one to compare with local metadata. No playlist changes.')

    def compare_musicbrainz(self):
        selected = self.mb_list.curselection()
        if not selected or selected[0] >= len(self.mb_results):
            messagebox.showinfo('Select a recording', 'Select one MusicBrainz result first.', parent=self)
            return
        row = self.mb_results[selected[0]]
        try:
            # Only artist and title are used for local matching. Release lists
            # may include multiple editions; never silently choose an album.
            entry = {'artist': row['artist'], 'title': row['title'], 'album': '',
                     'source': 'MusicBrainz recording ' + row['mbid']}
            matches = match_entries([entry], self._tracks())
            self._set_rows(matches, 'musicbrainz')
            self.summary.set(f"MusicBrainz {row['mbid']}: {matches[0]['status']} against loaded local track IDs. "
                             'Review editions and resolve ambiguity before optional Apply; no phone writes.')
        except MatchError as exc:
            messagebox.showerror('Cannot compare recording', str(exc), parent=self)

    def show_choices(self, event=None):
        selection = self.preview.curselection()
        if not selection:
            return
        row = self.rows[selection[0]]
        self.candidate_ids = row['candidate_ids'][:]
        labels = []
        for tid in self.candidate_ids:
            t = self.lookup[tid]
            labels.append(f"{t.get('artist', '')} — {t.get('title', '')} [{t.get('album', '')}]  |  ID: {tid}")
        self.candidate['values'] = labels
        if row.get('chosen_id') in self.candidate_ids:
            self.candidate.current(self.candidate_ids.index(row['chosen_id']))
        else:
            self.candidate.set('')

    def resolve(self):
        selected = self.preview.curselection()
        choice = self.candidate.current()
        if not selected or not (0 <= choice < len(getattr(self, 'candidate_ids', []))):
            messagebox.showinfo('Choose a candidate', 'Select a preview row and an actual local track ID.', parent=self)
            return
        row = self.rows[selected[0]]
        row['chosen_id'] = self.candidate_ids[choice]
        row['status'] = 'MATCH'
        self._set_rows_preserve_selection(selected[0])

    def _set_rows_preserve_selection(self, index):
        # Update only the row label, without invalidating the full preview.
        row = self.rows[index]
        e = row['entry']
        name = f"{e.get('artist', '')} — {e.get('title', '')}" if e.get('title') else e.get('path', '(untitled)')
        if e.get('album'):
            name += f" [{e['album']}]"
        self.preview.delete(index)
        self.preview.insert(index, f"{index+1:>3}. MATCH      {name}")
        self.preview.selection_set(index)
        self.preview.see(index)
        self.summary.set('Candidate selected from real local IDs. Review all rows before applying.')

    def apply(self):
        if not self.rows:
            messagebox.showinfo('Nothing to apply', 'Preview tracks first.', parent=self)
            return
        if _signature(self._tracks()) != self.snapshot_signature or self.app.selector.get() != self.playlist_name:
            messagebox.showerror('Preview stale', 'Library or selected playlist changed. Preview again.', parent=self)
            return
        pl = self.app.current_pl()
        if pl is None:
            messagebox.showerror('Choose playlist', 'Create or select a Music/Audiobook playlist first.', parent=self)
            return
        ids, duplicates, unresolved = resolved_ids(self.rows, existing=pl['track_ids'])
        if not ids:
            messagebox.showinfo('Nothing new', 'No unique resolved local track IDs to append.', parent=self)
            return
        summary = (f'Append {len(ids)} existing local track IDs to {pl["name"]!r} '
                   f'({"Audiobook" if pl.get("audiobook") else "Music"}) in the displayed order?\n\n'
                   f'{len(unresolved)} unresolved/missing rows and {len(duplicates)} duplicate/already-present '
                   'rows will NOT be added.\n\nThis edits the current in-memory playlist only; '
                   'Save As is separate. No phone changes or audio transfers.')
        if not messagebox.askyesno('Confirm reviewed proposal', summary, parent=self):
            return
        self.app._remember()
        count = insert_selected(pl, ids)
        if not count:
            self.app._forget_noop()
            return
        self.app.changed = True
        self.app.refresh_playlist()
        self.app.status.set(f'Appended {count} reviewed local track ID(s) in order (unsaved); '
                            f'{len(unresolved)} unresolved, {len(duplicates)} duplicates skipped. No phone changes.')
        self.destroy()
