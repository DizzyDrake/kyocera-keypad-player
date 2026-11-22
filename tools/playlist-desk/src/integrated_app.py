"""Single-window Windows/Linux Tkinter playlist editor + optional localhost model preview.

No ADB, audio I/O, phone access or installed app changes; explicit opt-in loopback model call only.
The bridge's provisional phone schema is NOT the owner's observed export format.
"""
import copy
import json
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from app import App
from bridge import BridgeError, load_json, phone_import_payload, IMPORT_FILENAME
from integration_core import attach_candidate, create_plan, create_preview, reattach_saved_playlists
from plan_recovery_candidate import recover_edited_pc
from playlist_core import PlaylistError, atomic_write, validate_output
from pc_file_add import append_pc_files, any_pending_files, playlist_has_pending_files
from two_pane_actions import insert_selected, remove_selected_indices, move_selected_block
from proposal_ui import ProposalDialog


class IntegratedApp(App):
    def __init__(self):
        super().__init__()
        self.title('Kyocera Playlist Desk + Bridge v0.16 — LOCAL-FIRST WORKSPACE')
        self.geometry('1120x700')
        self.minsize(900, 560)
        self.phone_snapshot = None
        self.phone_source = None
        self._undo = []
        self._drag = None
        self._drop_marker = None
        self._decorate()
        # Owner-requested two one-click type actions, retaining the name prompt.
        self.new_playlist_button.configure(text='New Music',
                                           command=lambda: self.new_playlist_kind(False))
        audiobook = ttk.Button(self.playlist_actions, text='New Audiobook',
                               command=lambda: self.new_playlist_kind(True))
        audiobook.pack(side='left', padx=3, before=self.playlist_actions.winfo_children()[1])
        # Native scrollbars keep long libraries usable without altering data.
        for widget in (self.library, self.plist):
            scroll = ttk.Scrollbar(widget.master, orient='vertical', command=widget.yview)
            scroll.grid(row=0, column=1, sticky='ns')
            widget.configure(yscrollcommand=scroll.set)
        # Both panes support Ctrl/Shift multi-selection. The mouse handlers
        # preserve an already selected block when beginning a drag.
        for pane, widget in (('library', self.library), ('playlist', self.plist)):
            widget.configure(selectmode=tk.EXTENDED, exportselection=False)
            widget.bind('<ButtonPress-1>', lambda e, pane=pane: self._pane_press(e, pane))
            widget.bind('<B1-Motion>', lambda e, pane=pane: self._pane_motion(e, pane))
            # Tk's default B1-Leave starts an after()-based ListboxAutoScan,
            # including horizontal drift and range selection. Suppress it while
            # preserving deliberate Shift/Ctrl clicks and ordinary scrolling.
            widget.bind('<B1-Leave>', self._stop_autoscan)
            widget.bind('<MouseWheel>', lambda e, w=widget: self._wheel_scroll(e, w))
            widget.bind('<Button-4>', lambda e, w=widget: self._wheel_scroll(e, w))
            widget.bind('<Button-5>', lambda e, w=widget: self._wheel_scroll(e, w))
            widget.bind('<ButtonRelease-1>', lambda e, pane=pane: self._pane_release(e, pane))
            widget.bind('<Control-a>', lambda e, w=widget: self._select_all(e, w))
        children = self.winfo_children()
        main = children[1]
        header = ttk.Frame(self, style='Header.TFrame')
        header.pack(before=children[0], fill='x')
        ttk.Label(header, text='PLAYLIST DESK', style='Title.TLabel').pack(side='left', padx=(15, 12), pady=12)
        ttk.Label(header, text='Organize • Preview • Export', style='HeaderSub.TLabel').pack(side='left')
        ttk.Label(header, text='OFFLINE  ·  LOCAL WORKSPACE', style='HeaderSub.TLabel').pack(side='right', padx=16)
        bridgebar = ttk.Frame(self)
        bridgebar.pack(before=main, fill='x', padx=12, pady=(4, 7))
        for label, action in (
            ('Load phone snapshot JSON…', self.attach_phone),
            ('Open saved plan JSON…', self.open_saved_plan),
            ('Stage PC audio files…', self.add_pc_audio_files),
            ('Save offline plan…', self.save_plan),
            ('Save simulated result…', self.save_preview),
            ('Create phone import JSON…', self.create_phone_import),
            ('↶ Undo last edit', self.undo_last),
        ):
            ttk.Button(bridgebar, text=label, command=action).pack(side='left', padx=(0, 7))
        matchbar = ttk.Frame(self)
        matchbar.pack(before=main, fill='x', padx=12, pady=(0, 5))
        ttk.Button(matchbar, text='Find by artist / album or rebuild a pasted playlist…',
                   command=self.open_match_dialog).pack(side='left')
        ttk.Label(matchbar, text='Review local track IDs; optional opt-in localhost Gemma only').pack(
            side='left', padx=12)
        self._drop_marker = tk.Frame(self.plist, background='#713E46', height=3,
                                     borderwidth=0)
        self.kind_label = ttk.Label(bridgebar, text='Playlist type: —')
        self.kind_label.pack(side='right', padx=10)
        guide = ttk.Label(self, text='LIBRARY  →  PLAYLIST: add selected tracks     •     '
                          'PLAYLIST  →  LIBRARY: remove playlist references only     •     '
                          'PLAYLIST  →  PLAYLIST: reorder selected tracks', style='Guide.TLabel')
        guide.pack(before=main, fill='x', padx=12, pady=(0, 5))
        self.status.set('Offline editor • Plain click selects one; Shift range; Ctrl toggles; drag a group • '
                        'drag selected rows or use buttons • no files transferred.')

    def open_match_dialog(self):
        if self.data is None:
            messagebox.showinfo('Load metadata first', 'Load a metadata JSON or phone snapshot before matching playlists.')
            return
        ProposalDialog(self)

    def _decorate(self):
        """Readable, restrained desktop polish; no external theme dependency."""
        style = ttk.Style(self)
        style.theme_use('clam')
        font_family = 'DejaVu Sans' if os.name == 'posix' else 'Segoe UI'
        # Source-grounded Dumbplayer palette from DEV8 KeypadPlayerActivity.
        self.configure(background='#F5F0EB')
        style.configure('TFrame', background='#F5F0EB')
        style.configure('Header.TFrame', background='#713E46')
        style.configure('Title.TLabel', background='#713E46', foreground='#F5F0EB',
                        font=(font_family, 16, 'bold'))
        style.configure('HeaderSub.TLabel', background='#713E46', foreground='#F5F0EB',
                        font=(font_family, 10))
        style.configure('TLabel', background='#F5F0EB', foreground='#252022', font=(font_family, 10))
        style.configure('Guide.TLabel', background='#E9DCD8', foreground='#252022',
                        padding=(10, 7), font=(font_family, 10, 'bold'))
        style.configure('TButton', background='#E9DCD8', foreground='#252022',
                        padding=(10, 7), font=(font_family, 10))
        style.map('TButton', background=[('active', '#D6A6AD'), ('pressed', '#C98B96')])
        style.configure('TEntry', padding=5)
        style.configure('TCombobox', padding=5)
        for widget in (self.library, self.plist):
            widget.configure(font=(font_family, 11), background='#FFFFFF',
                             foreground='#252022', selectbackground='#D6A6AD',
                             selectforeground='#252022', highlightthickness=1,
                             highlightbackground='#713E46', activestyle='none')

    def _cancel_autoscan(self):
        # Also cancel any repeat scheduled by an earlier class binding.
        self.tk.call('tk::CancelRepeat')

    def _stop_autoscan(self, event):
        self._cancel_autoscan()
        return 'break'

    def _wheel_scroll(self, event, widget):
        self._cancel_autoscan()
        if getattr(event, 'num', None) == 4:
            delta = -3
        elif getattr(event, 'num', None) == 5:
            delta = 3
        else:
            wheel = getattr(event, 'delta', 0)
            if not wheel:
                return 'break'
            delta = -max(1, round(abs(wheel) / 120)) if wheel > 0 else max(1, round(abs(wheel) / 120))
        widget.yview_scroll(delta, 'units')
        return 'break'

    def _select_all(self, event, widget):
        widget.selection_set(0, tk.END)
        return 'break'

    def _remember(self):
        if self.data is not None:
            self._undo.append((copy.deepcopy(self.data), self.selector.get(), self.changed))
            if len(self._undo) > 20:
                self._undo.pop(0)

    def _forget_noop(self):
        if self._undo:
            self._undo.pop()

    def undo_last(self):
        if not self._undo:
            self.status.set('No recent playlist edit to undo in this session.')
            return
        self.data, selected, self.changed = self._undo.pop()
        self.update_selector(selected)
        self.refresh_library()
        self.refresh_playlist()
        self.status.set('Undid last playlist edit (in memory). No source file changed.')

    def _pane_press(self, event, pane):
        widget = self.library if pane == 'library' else self.plist
        self._drag = None
        if not self.data or widget.size() == 0 or not (0 <= event.y < widget.winfo_height()):
            return
        index = widget.nearest(event.y)
        if not 0 <= index < widget.size():
            return
        # Ctrl and Shift retain Tk's normal selection semantics.
        if event.state & 0x0005:
            return
        selected = list(widget.curselection())
        if index not in selected:
            widget.selection_clear(0, tk.END)
            widget.selection_set(index)
            selected = [index]
        widget.focus_set()
        self._drag = {'pane': pane, 'playlist': self.selector.get(),
                      'indices': selected, 'index': index, 'x': event.x_root, 'y': event.y_root,
                      'xview': widget.xview()[0]}
        return 'break'

    def _pane_motion(self, event, pane):
        if self._drag and self._drag['pane'] == pane:
            self._update_drop_indicator(event, pane)
        # A Shift/Ctrl press uses Tk's class handler to select/toggle once,
        # so _drag is deliberately None. But letting its subsequent B1-Motion
        # reach Tk's ListboxMotion extends the selection when the pointer moves
        # during a wheel/scroll interaction. Keep Shift-click and Ctrl-click,
        # but never let held-button motion silently select additional rows.
        # Plain group dragging already has our explicit drop handling above.
        return 'break'

    def _drop_target(self, event):
        widget = self.winfo_containing(event.x_root, event.y_root)
        # The thin insertion marker is a child of the playlist listbox.
        if widget is self._drop_marker:
            widget = self.plist
        if widget is self.library:
            return 'library', widget
        if widget is self.plist:
            return 'playlist', widget
        return None, None

    def _drop_boundary(self, widget, event):
        y = event.y_root - widget.winfo_rooty()
        if widget.size() == 0:
            return 0
        if y <= 0:
            return 0
        if y >= widget.winfo_height():
            return widget.size()
        idx = widget.nearest(y)
        # Lower half of a row inserts after it, upper half before it.
        bbox = widget.bbox(idx)
        if bbox and y >= bbox[1] + bbox[3] / 2:
            idx += 1
        return idx

    def _hide_drop_indicator(self):
        if self._drop_marker is not None:
            self._drop_marker.place_forget()

    def _update_drop_indicator(self, event, pane):
        if self._drop_marker is None:
            return
        target, widget = self._drop_target(event)
        if target != 'playlist' or pane not in ('library', 'playlist'):
            self._hide_drop_indicator()
            return
        boundary = self._drop_boundary(widget, event)
        if widget.size() == 0:
            y = 2
        elif boundary < widget.size():
            bbox = widget.bbox(boundary)
            y = bbox[1] if bbox else (2 if boundary == 0 else widget.winfo_height() - 4)
        else:
            bbox = widget.bbox(widget.size() - 1)
            y = bbox[1] + bbox[3] if bbox else widget.winfo_height() - 4
        y = max(1, min(widget.winfo_height() - 4, y))
        self._drop_marker.place(x=1, y=y, width=max(2, widget.winfo_width() - 2), height=3)
        self._drop_marker.lift()

    def _pane_release(self, event, pane):
        drag = self._drag
        self._drag = None
        self._cancel_autoscan()
        self._hide_drop_indicator()
        if not drag or drag['pane'] != pane:
            return
        if abs(event.x_root - drag['x']) + abs(event.y_root - drag['y']) < 7:
            # We delayed collapsing a selected group until mouse-up so that
            # beginning a drag on one of its members retains the whole group.
            # A genuine plain click must instead select exactly one row and
            # set Tk's anchor for the very next Shift-click in either pane.
            source = self.library if pane == 'library' else self.plist
            if 0 <= drag['index'] < source.size():
                source.selection_clear(0, tk.END)
                source.selection_set(drag['index'])
                source.selection_anchor(drag['index'])
                source.activate(drag['index'])
                source.focus_set()
            return 'break'
        if drag['playlist'] != self.selector.get():
            self.status.set('Drop cancelled: selected playlist changed.')
            return 'break'
        target, widget = self._drop_target(event)
        if pane == 'library' and target != 'playlist':
            # An unsupported library-internal drag is a no-op; restore the
            # original horizontal position instead of leaving a shifted pane.
            self.library.xview_moveto(drag['xview'])
        if target is None:
            self.status.set('Drop outside a list: no changes.')
            return 'break'
        pl = self.current_pl()
        if pl is None:
            return 'break'
        indices = drag['indices']
        if pane == 'library' and target == 'playlist':
            tids = [self.filtered[i] for i in indices if 0 <= i < len(self.filtered)]
            if tids:
                self._remember()
                count = insert_selected(pl, tids, self._drop_boundary(widget, event))
                if count:
                    self.changed = True
                    self.refresh_playlist()
                else:
                    self._forget_noop()
                self.status.set(f'Added {count} new library track(s) (unsaved); already-listed tracks skipped.')
        elif pane == 'playlist' and target == 'library':
            self._remember()
            removed = remove_selected_indices(pl, indices)
            if removed:
                self.changed = True
                self._prune_pending(removed)
                self.refresh_library()
                self.refresh_playlist()
                self.status.set(f'Removed {len(removed)} playlist reference(s) only; no audio deleted (unsaved).')
            else:
                self._forget_noop()
        elif pane == 'playlist' and target == 'playlist':
            self._remember()
            new_indices = move_selected_block(pl, indices, self._drop_boundary(widget, event))
            if new_indices:
                self.changed = True
                self.refresh_playlist()
                for i in new_indices:
                    self.plist.selection_set(i)
                self.plist.see(new_indices[0])
                self.status.set(f'Reordered {len(new_indices)} selected track(s) (unsaved).')
            else:
                self._forget_noop()
        return 'break'

    def new_playlist(self):
        # Legacy command remains a Music shortcut; explicit buttons control type.
        return self.new_playlist_kind(False)

    def new_playlist_kind(self, audiobook=False):
        """Create an explicitly typed playlist with only a name prompt."""
        if self.data is None:
            return
        label = 'Audiobook' if audiobook else 'Music'
        name = simpledialog.askstring('New ' + label + ' playlist',
                                      'Playlist name:', parent=self)
        if name is None:
            return
        self._remember()
        try:
            pl = self._create_typed_playlist(name, audiobook=audiobook)
        except PlaylistError as exc:
            self._forget_noop()
            messagebox.showerror('Cannot create playlist', str(exc))
            return
        self.changed = True
        self.update_selector(pl['name'])
        self.status.set(label + ' playlist created (unsaved): ' + pl['name'])

    def _create_typed_playlist(self, name, audiobook=False):
        """Pure metadata mutation, validated by existing playlist_core."""
        from playlist_core import create_playlist
        if type(audiobook) is not bool:
            raise PlaylistError('playlist type must be Music or Audiobook')
        pl = create_playlist(self.data, name)
        pl['audiobook'] = audiobook
        return pl

    def _prune_pending(self, removed):
        referenced = {tid for p in self.data['playlists'] for tid in p['track_ids']}
        self.data['tracks'] = [t for t in self.data['tracks'] if not (
            t['id'] in removed and t['id'] not in referenced and
            t.get('pc_status') == 'pending-local-not-on-phone')]

    def add_selected(self):
        pl = self.current_pl()
        selected = self.library.curselection()
        if pl is None or not selected:
            return
        tids = [self.filtered[i] for i in selected if i < len(self.filtered)]
        self._remember()
        count = insert_selected(pl, tids)
        if count:
            self.changed = True
            self.refresh_playlist()
            self.plist.selection_set(len(pl['track_ids']) - count, tk.END)
        else:
            self._forget_noop()
        self.status.set(f'Added {count} new library track(s) (unsaved); already-listed tracks skipped.')

    def remove_selected(self):
        pl = self.current_pl()
        selected = self.plist.curselection()
        if pl is None or not selected:
            return
        self._remember()
        removed = remove_selected_indices(pl, selected)
        self._prune_pending(removed)
        self.changed = True
        self.refresh_library()
        self.refresh_playlist()
        self.status.set(f'Removed {len(removed)} playlist reference(s), no audio files touched (unsaved).')

    def shift(self, delta):
        pl = self.current_pl()
        selected = list(self.plist.curselection())
        if pl is None or not selected:
            return
        # Move a contiguous selection by one row; noncontiguous groups move as
        # a block, retaining selected order, and are undoable.
        boundary = min(selected) + delta if delta < 0 else max(selected) + delta + 1
        if boundary < 0 or boundary > len(pl['track_ids']):
            return
        self._remember()
        indices = move_selected_block(pl, selected, boundary)
        if indices:
            self.changed = True
            self.refresh_playlist()
            for i in indices:
                self.plist.selection_set(i)
            self.plist.see(indices[0])
            self.status.set(f'Moved {len(indices)} selected track(s) (unsaved).')
        else:
            self._forget_noop()

    def add_pc_audio_files(self):
        pl = self.current_pl()
        if pl is None:
            messagebox.showinfo('Choose playlist', 'Open metadata and choose a playlist before adding PC audio files.')
            return
        selected = filedialog.askopenfilenames(
            title='Select local audio files (staged only; no transfer)',
            filetypes=[('Audio files', '*.mp3 *.m4a *.aac *.ogg *.opus *.flac *.wav *.wma *.mp4 *.m4b'),
                       ('All files', '*')])
        if not selected:
            return
        try:
            new_data, count, skipped = append_pc_files(self.data, pl['name'], selected)
        except (PlaylistError, OSError, ValueError) as exc:
            messagebox.showerror('PC files not added', str(exc))
            return
        if count:
            self._remember()
            self.data = new_data
            self.changed = True
            self.refresh_library()
            self.refresh_playlist()
            self.plist.selection_set('end')
            self.plist.see('end')
        self.status.set(f'{count} local PC file(s) staged in playlist; {skipped} duplicate(s) skipped. '
                        'NOT on phone. Save As JSON to retain; bridge plan refuses pending files.')

    def refresh_library(self):
        super().refresh_library()
        if self.data is None:
            return
        lookup = {t['id']: t for t in self.data['tracks']}
        for i, tid in enumerate(self.filtered):
            if lookup[tid].get('pc_status') == 'pending-local-not-on-phone':
                self.library.delete(i)
                self.library.insert(i, '[PC ONLY — NOT ON PHONE] ' + lookup[tid]['title'])

    def refresh_playlist(self):
        super().refresh_playlist()
        pl = self.current_pl()
        if hasattr(self, 'kind_label'):
            self.kind_label.configure(text=('Playlist type: —' if pl is None else
                'Playlist type: ' + ('AUDIOBOOK' if pl.get('audiobook', False) else 'MUSIC')))
        if pl is None:
            return
        lookup = {t['id']: t for t in self.data['tracks']}
        for i, tid in enumerate(pl['track_ids']):
            if lookup[tid].get('pc_status') == 'pending-local-not-on-phone':
                self.plist.delete(i)
                self.plist.insert(i, f'{i+1:>3}. [PC ONLY — NOT ON PHONE] {lookup[tid]["title"]}')

    def export_m3u8(self):
        pl = self.current_pl()
        if pl and playlist_has_pending_files(self.data, pl['name']):
            messagebox.showerror('Cannot export pending PC files',
                'This playlist contains PC-only files not mapped to phone paths. '
                'Save As JSON to preserve the staged list; M3U8 export is disabled for this playlist.')
            return
        return super().export_m3u8()

    def open_file(self):
        # Loading a different editor file must not retain an unrelated phone
        # snapshot; reattach the exact snapshot explicitly before planning.
        previous = self.data
        super().open_file()
        if self.data is not previous:
            self._undo.clear()
            self.phone_snapshot = None
            self.phone_source = None

    def open_saved_plan(self):
        """Recover edited playlists only against an explicitly loaded matching snapshot.

        No write/import. Reject stale plans without touching the current editor.
        """
        if self.phone_snapshot is None:
            messagebox.showinfo('Load phone snapshot first',
                'Load the matching phone snapshot JSON before opening a saved plan.')
            return
        path = filedialog.askopenfilename(title='Open saved bridge plan JSON',
                                          filetypes=[('Bridge plan JSON', '*.json')])
        if not path:
            return
        try:
            validate_output(path)
            saved = load_json(path)
            recovered = recover_edited_pc(self.phone_snapshot, saved)
        except (BridgeError, PlaylistError, OSError, ValueError, TypeError) as exc:
            messagebox.showerror('Cannot recover saved plan', str(exc))
            return
        if not self.confirm_discard():
            return
        # Preserve the snapshot provenance; recovered edits are unsaved workspace
        # state, never a phone import file and never a Save-As overwrite target.
        self.data = recovered
        self.source = None
        self.changed = True
        self._undo.clear()
        self.update_selector(recovered['playlists'][0]['name'] if recovered['playlists'] else None)
        self.refresh_library()
        self.refresh_playlist()
        self.status.set('Recovered saved plan edits (unsaved): ' + Path(path).name +
                        ' • phone import still requires explicit export.')

    def attach_phone(self):
        path = filedialog.askopenfilename(
            title='Choose a fictional PROVISIONAL phone snapshot',
            filetypes=[('JSON snapshot', '*.json')])
        if not path:
            return
        try:
            validate_output(path)
            phone = load_json(path)
            pc, retained = attach_candidate(phone, self.data)
            # A preexisting Save As JSON is reusable even when its source phone
            # snapshot is older. Require explicit approval and exact relative
            # media paths; never guess a track from title or artist.
            if not retained and self.data is not None and self.data.get('playlists'):
                try:
                    recovered = reattach_saved_playlists(phone, self.data)
                except BridgeError as exc:
                    if not messagebox.askyesno('Saved playlists cannot be fully matched',
                            str(exc) + '\n\nDiscard the unmatched editor playlists and load just the phone snapshot instead?'):
                        return
                else:
                    if messagebox.askyesno('Use your already-saved playlists?',
                            'The current PC playlists can be matched to this phone snapshot by '
                            'exact relative music paths. Reuse those playlist names and track order? '
                            'No files or phone data are changed by this step.'):
                        pc = recovered
                        retained = True
            if not retained:
                if any_pending_files(self.data):
                    if not messagebox.askyesno('PC-only tracks will leave this editor view',
                            'The selected phone snapshot has no matching PC-only tracks. Reattaching it will remove the staged PC entries from this window. Save As JSON first if you want to keep them. Continue?'):
                        return
                elif not self.confirm_discard():
                    return
            # Only mutate GUI state after all validation and confirmation.
            self.data = pc
            self._undo.clear()
            if not retained:
                self.changed = False
                self.source = path  # original snapshot cannot be Save-As target
            self.phone_snapshot = copy.deepcopy(phone)
            self.phone_source = path
            self.update_selector(pc['playlists'][0]['name'] if pc['playlists'] else None)
            self.refresh_library()
            self.refresh_playlist()
            self.status.set(('Your existing playlists are retained against the phone snapshot: ' if retained else
                             'Loaded phone snapshot into editor: ') + Path(path).name)
        except (BridgeError, PlaylistError, OSError, ValueError, TypeError) as exc:
            messagebox.showerror('Cannot load phone snapshot', str(exc))

    def _new_json_destination(self):
        target = filedialog.asksaveasfilename(
            title='Choose a NEW output JSON (no overwrite)',
            defaultextension='.json', filetypes=[('JSON', '*.json')])
        if not target:
            return None
        path = validate_output(target)
        if path.exists():
            raise PlaylistError('Output already exists. Choose a NEW filename; no overwrite is allowed for bridge results.')
        if self.phone_source and os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(self.phone_source)):
            raise PlaylistError('Refusing to replace the original phone snapshot')
        if self.source and os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(self.source)):
            raise PlaylistError('Refusing to replace the imported editor JSON')
        return path

    def _save_bridge_result(self, operation):
        if self.phone_snapshot is None or self.data is None:
            messagebox.showinfo('Load snapshot first', 'Load a fictional provisional phone snapshot before planning or simulating.')
            return
        if any_pending_files(self.data):
            messagebox.showerror('PC-only files cannot be sent to phone',
                'Remove pending PC-only tracks before planning or importing. PC-only audio has no matching phone track identity.')
            return
        try:
            result = create_plan(self.phone_snapshot, self.data) if operation == 'plan' else create_preview(self.phone_snapshot, self.data)
            destination = self._new_json_destination()
            if destination is None:
                return
            atomic_write(destination, (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
            if operation == 'plan':
                changed = [x for x in result['operations'] if x['action'] not in ('UNCHANGED', 'PRESERVE_UNMENTIONED')]
                note = f'Wrote OFFLINE plan ({len(changed)} changed playlists)'
            else:
                note = f'Wrote OFFLINE simulated revision {result["revision"]}'
            self.status.set(note + ': ' + destination.name + '. NOT transferred to phone.')
        except (BridgeError, PlaylistError, OSError, ValueError, TypeError) as exc:
            messagebox.showerror('Bridge output refused', str(exc))

    def create_phone_import(self):
        """Source-only handoff: writes JSON for an explicit later ADB push.

        PC-only staged audio cannot be copied by this metadata-only workflow.
        The phone importer replaces playlists and resets playback positions.
        """
        if self.phone_snapshot is None or self.data is None:
            messagebox.showinfo('Load phone snapshot',
                                'Attach a current Dumbplayer phone snapshot before exporting.')
            return
        if any_pending_files(self.data):
            messagebox.showerror('PC-only tracks are unavailable on phone',
                                 'Remove PC-only staged tracks before exporting.')
            return
        if not messagebox.askyesno('Create phone playlist import?',
                'The phone will replace its playlists and may reset music/audiobook positions if their tracks were removed '
                'when you confirm the import on the phone. No audio files will be copied or removed. '
                'Only create this file if that is acceptable.'):
            return
        try:
            payload = phone_import_payload(self.phone_snapshot, self.data)
            destination = self._new_json_destination()
            if destination is None:
                return
            atomic_write(destination, (json.dumps(payload, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
            self.status.set('Created phone import JSON: '+destination.name+
                '. Use ADB to push it as '+IMPORT_FILENAME+'; then confirm on Dumbplayer.')
        except (BridgeError, PlaylistError, OSError, TypeError, ValueError) as exc:
            messagebox.showerror('Cannot create phone import', str(exc))

    def save_plan(self):
        self._save_bridge_result('plan')

    def save_preview(self):
        self._save_bridge_result('simulate')


if __name__ == '__main__':
    IntegratedApp().mainloop()
