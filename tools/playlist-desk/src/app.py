"""Small keyboard-friendly Windows 10 Tk GUI; no phone or audio access."""
import copy
import os
import re
import tkinter as tk
from tkinter import filedialog,messagebox,simpledialog,ttk
from pathlib import Path
from playlist_core import load,encode,m3u8,move,add,remove,PlaylistError,validate_output,create_playlist,rename_playlist,delete_playlist,atomic_write
from duplicate_candidates import candidate_groups, iter_candidate_pairs

def matches_library_query(track, query):
    """Match track metadata without altering playlists or any audio files.

    Existing literal and NOT searches remain unchanged: 'blue jazz',
    'jazz NOT live NOT remix'. With commas, positive phrases are alternatives
    (OR); every NOT phrase excludes matches (AND), for example:
    'jazz, blues, NOT live, NOT remix'. A bare/incomplete NOT keeps the query
    literal rather than silently broadening matches.
    """
    haystack = ' '.join(str(track.get(k, '')) for k in
                        ('title', 'artist', 'album', 'genre', 'path')).casefold()
    q = query.strip()
    # Preserve all existing no-comma behavior (including malformed NOT input).
    def split_not(expression):
        return re.split(r'(?i)(?:^|\s+)NOT(?=\s|$)', expression)

    if ',' not in q:
        parts = split_not(q)
        if len(parts) == 1 or any(not part.strip() for part in parts[1:]):
            return q.casefold() in haystack
        positive = parts[0].strip().casefold()
        exclusions = [part.strip().casefold() for part in parts[1:]]
        return (not positive or positive in haystack) and all(term not in haystack for term in exclusions)

    # Commas join alternatives while NOT exclusions apply to every alternative.
    # Whitespace/empty comma slots are ignored as the person types a filter.
    positives = []
    exclusions = []
    for clause in (part.strip() for part in q.split(',')):
        if not clause:
            continue
        parts = split_not(clause)
        if len(parts) == 1:
            positives.append(clause.casefold())
        elif any(not part.strip() for part in parts[1:]):
            return q.casefold() in haystack  # incomplete operator: safe literal
        else:
            if parts[0].strip():
                positives.append(parts[0].strip().casefold())
            exclusions.extend(part.strip().casefold() for part in parts[1:])
    return (not positives or any(term in haystack for term in positives)) and all(
        term not in haystack for term in exclusions)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Kyocera Playlist Desk v0.2 — OFFLINE metadata editor')
        self.geometry('930x610')
        self.data=None;self.source=None;self.changed=False
        top=ttk.Frame(self);top.pack(fill='x',padx=8,pady=6)
        for label,fn in [('Open metadata JSON',self.open_file),('Save As JSON',self.save_file),('Export M3U8',self.export_m3u8)]:
            ttk.Button(top,text=label,command=fn).pack(side='left',padx=3)
        self.duplicate_review_button=ttk.Button(top,text='Review possible duplicates',command=self.review_duplicates)
        self.duplicate_review_button.pack(side='left',padx=3)
        ttk.Label(top,text='No ADB / no phone changes').pack(side='right')
        main=ttk.Frame(self);main.pack(fill='both',expand=True,padx=8,pady=4)
        main.columnconfigure(0,weight=1);main.columnconfigure(1,weight=1);main.rowconfigure(1,weight=1)
        filterbar=ttk.Frame(main);filterbar.grid(row=0,column=0,sticky='ew')
        ttk.Label(filterbar,text='Filter (comma OR; NOT excludes):').pack(side='left')
        self.query=tk.StringVar();entry=ttk.Entry(filterbar,textvariable=self.query,width=32);entry.pack(side='left',fill='x',expand=True,padx=5)
        self.query.trace_add('write',lambda *_:self.refresh_library())
        ttk.Label(main,text='Playlist (manual order)').grid(row=0,column=1,sticky='w')
        left=ttk.Frame(main);left.grid(row=1,column=0,sticky='nsew',padx=(0,7))
        right=ttk.Frame(main);right.grid(row=1,column=1,sticky='nsew')
        for f in (left,right):f.rowconfigure(0,weight=1);f.columnconfigure(0,weight=1)
        self.library=tk.Listbox(left,exportselection=False);self.library.grid(row=0,column=0,sticky='nsew')
        self.plist=tk.Listbox(right,exportselection=False);self.plist.grid(row=0,column=0,sticky='nsew')
        selector_row=ttk.Frame(right);selector_row.grid(row=1,column=0,sticky='ew',pady=3)
        selector_row.columnconfigure(1,weight=1)
        self.previous_playlist_button=ttk.Button(selector_row,text='◀',width=3,command=lambda:self.step_playlist(-1))
        self.previous_playlist_button.grid(row=0,column=0,padx=(0,3))
        self.selector=ttk.Combobox(selector_row,state='readonly');self.selector.grid(row=0,column=1,sticky='ew')
        self.selector.bind('<<ComboboxSelected>>',lambda _: (self.refresh_playlist(),self.update_playlist_navigation()))
        self.selector.bind('<Alt-Left>',lambda _:self.step_playlist(-1))
        self.selector.bind('<Alt-Right>',lambda _:self.step_playlist(1))
        self.next_playlist_button=ttk.Button(selector_row,text='▶',width=3,command=lambda:self.step_playlist(1))
        self.next_playlist_button.grid(row=0,column=2,padx=(3,0))
        self.playlist_position=tk.StringVar(value='0 / 0')
        ttk.Label(selector_row,textvariable=self.playlist_position).grid(row=0,column=3,padx=(5,0))
        playlist_actions=ttk.Frame(right);playlist_actions.grid(row=2,column=0,sticky='ew',pady=3)
        self.playlist_actions=playlist_actions
        for name,fn in [('New playlist',self.new_playlist),('Rename',self.rename_selected_playlist),('Delete',self.delete_selected_playlist)]:
            button=ttk.Button(playlist_actions,text=name,command=fn)
            button.pack(side='left',padx=3)
            if name == 'New playlist':
                self.new_playlist_button=button
        buttons=ttk.Frame(main);buttons.grid(row=2,column=0,columnspan=2,pady=7)
        for name,fn in [('Add selected →',self.add_selected),('Remove',self.remove_selected),('↑ Move up',lambda:self.shift(-1)),('↓ Move down',lambda:self.shift(1))]:
            ttk.Button(buttons,text=name,command=fn).pack(side='left',padx=6)
        self.status=tk.StringVar(value='Open a metadata JSON fixture. Ctrl+O open; Ctrl+Shift+S Save As. No audio copied.')
        ttk.Label(self,textvariable=self.status,wraplength=900).pack(fill='x',padx=8,pady=7)
        self.bind_all('<Control-o>',lambda _:self.open_file())
        self.bind_all('<Control-Shift-S>',lambda _:self.save_file())
        self.protocol('WM_DELETE_WINDOW',self.close)
    def review_duplicates(self):
        """Show a read-only metadata shortlist; never select files for deletion."""
        if self.data is None:
            messagebox.showinfo('Possible duplicates', 'Open a metadata JSON first.', parent=self)
            return
        # Reject malformed metadata before opening a review dialog or advancing the iterator.
        # Keep the existing lazy paging path intact for valid catalog data.
        tracks = self.data.get('tracks') if isinstance(self.data, dict) else None
        if not isinstance(tracks, list) or any(not isinstance(track, dict) for track in tracks):
            messagebox.showerror('Cannot review duplicates',
                'Metadata tracks must be a list of track objects.', parent=self)
            return
        # A lazy iterator avoids materializing O(n^2) pairs in memory.
        pair_iterator=iter_candidate_pairs(tracks)
        page_size=200
        page=[]
        exhausted=False
        def take_page():
            nonlocal exhausted
            result=[]
            for _ in range(page_size):
                try: result.append(next(pair_iterator))
                except StopIteration:
                    exhausted=True
                    break
            return result
        page=take_page()
        dialog=tk.Toplevel(self)
        dialog.title('Possible duplicate songs — review only')
        dialog.geometry('960x430')
        dialog.transient(self)
        dialog.columnconfigure(0,weight=1)
        dialog.rowconfigure(1,weight=1)
        heading=tk.StringVar()
        ttk.Label(dialog,textvariable=heading,wraplength=910).grid(
            row=0,column=0,sticky='ew',padx=10,pady=10)
        area=ttk.Frame(dialog)
        area.grid(row=1,column=0,sticky='nsew',padx=10)
        area.columnconfigure(0,weight=1)
        area.rowconfigure(0,weight=1)
        columns=('artist','title','difference','first','second')
        table=ttk.Treeview(area,columns=columns,show='headings',selectmode='browse')
        widths=(125,160,85,260,260)
        for col,width in zip(columns,widths):
            table.heading(col,text={'artist':'Artist','title':'Title','difference':'Difference','first':'File A (path)','second':'File B (path)'}[col])
            table.column(col,width=width,minwidth=60,stretch=col in ('first','second'))
        page_number=1
        def show_page(items):
            table.delete(*table.get_children())
            for pair in items:
                table.insert('', 'end', values=(pair['artist_key'],pair['title_key'],
                    str(pair['duration_difference_ms'])+' ms',
                    str(pair['paths'][0] or ''),str(pair['paths'][1] or '')))
            first=(page_number-1)*page_size+1 if items else 0
            last=(page_number-1)*page_size+len(items)
            heading.set(f'Possible duplicate pairs {first}–{last} (page {page_number}). '
                'Metadata only; NOT proven duplicates. No files are changed.')
            next_button.configure(state='disabled' if exhausted else 'normal')
            previous_button.configure(state='normal' if page_number>1 else 'disabled')
        def next_page():
            nonlocal page_number, page
            if exhausted:return
            following=take_page()
            if following:
                page_number+=1
                page=following
            show_page(page)
        def previous_page():
            nonlocal page_number, page, pair_iterator, exhausted
            if page_number<=1:return
            target=page_number-1
            pair_iterator=iter_candidate_pairs(tracks)
            exhausted=False
            for _ in range(target):
                page=take_page()
            page_number=target
            show_page(page)
        navigation=ttk.Frame(dialog)
        navigation.grid(row=4,column=0,pady=(0,10))
        previous_button=ttk.Button(navigation,text='Previous 200',command=previous_page)
        previous_button.pack(side='left',padx=6)
        next_button=ttk.Button(navigation,text='Next 200',command=next_page)
        next_button.pack(side='left',padx=6)
        show_page(page)
        table.grid(row=0,column=0,sticky='nsew')
        scroll=ttk.Scrollbar(area,orient='vertical',command=table.yview)
        scroll.grid(row=0,column=1,sticky='ns')
        table.configure(yscrollcommand=scroll.set)
        ttk.Label(dialog,text='Metadata may match different recordings, live versions or re-encodes. '
            'Inspect audio separately before making any decision.',wraplength=910).grid(
            row=2,column=0,sticky='ew',padx=10,pady=6)
        ttk.Button(dialog,text='Close review',command=dialog.destroy).grid(row=3,column=0,pady=(0,10))
        return dialog
    def confirm_discard(self):
        return not self.changed or messagebox.askyesno('Unsaved edits','Discard unsaved playlist edits?')
    def close(self):
        if self.confirm_discard():self.destroy()
    def open_file(self):
        if not self.confirm_discard():return
        path=filedialog.askopenfilename(filetypes=[('JSON metadata','*.json')])
        if not path:return
        try:
            validate_output(path)
            data=load(path)
        except Exception as e:
            messagebox.showerror('Cannot open metadata',str(e));return
        self.data=copy.deepcopy(data);self.source=path;self.changed=False
        self.update_selector(data['playlists'][0]['name'] if data['playlists'] else None)
        self.refresh_library();self.refresh_playlist();self.status.set('Loaded metadata only: '+Path(path).name)
    def update_selector(self, desired=None):
        names=[p['name'] for p in self.data['playlists']] if self.data else []
        self.selector['values']=names
        if desired in names:self.selector.set(desired)
        elif names:self.selector.current(0)
        else:self.selector.set('')
        self.refresh_playlist()
        self.update_playlist_navigation()
    def update_playlist_navigation(self):
        names=list(self.selector['values'])
        index=names.index(self.selector.get()) if self.selector.get() in names else -1
        self.playlist_position.set(f'{index+1 if index>=0 else 0} / {len(names)}')
        state='normal' if len(names)>1 else 'disabled'
        self.previous_playlist_button.configure(state=state)
        self.next_playlist_button.configure(state=state)
    def step_playlist(self, delta):
        names=list(self.selector['values'])
        if len(names)<2:return 'break'
        try:index=names.index(self.selector.get())
        except ValueError:index=0
        self.selector.current((index+delta)%len(names))
        self.refresh_playlist()
        self.update_playlist_navigation()
        return 'break'
    def new_playlist(self):
        if self.data is None:return
        name=simpledialog.askstring('New playlist','Playlist name:',parent=self)
        if name is None:return
        try:
            create_playlist(self.data,name)
        except PlaylistError as e:
            messagebox.showerror('Cannot create playlist',str(e));return
        self.changed=True;self.update_selector(name);self.status.set('Created playlist (unsaved): '+name)
    def rename_selected_playlist(self):
        pl=self.current_pl()
        if pl is None:return
        old=pl['name']
        name=simpledialog.askstring('Rename playlist','New playlist name:',initialvalue=old,parent=self)
        if name is None or name==old:return
        try:
            rename_playlist(self.data,old,name)
        except PlaylistError as e:
            messagebox.showerror('Cannot rename playlist',str(e));return
        self.changed=True;self.update_selector(name);self.status.set('Renamed playlist (unsaved): '+name)
    def delete_selected_playlist(self):
        pl=self.current_pl()
        if pl is None:return
        name=pl['name']
        if not messagebox.askyesno('Delete playlist?',
                'Delete playlist '+repr(name)+' from the current editor?\nNo audio files are affected. Save As is required to persist.'):
            return
        delete_playlist(self.data,name);self.changed=True
        self.update_selector();self.status.set('Deleted playlist (unsaved): '+name)
    def current_pl(self):
        if self.data is None:return None
        return next((p for p in self.data['playlists'] if p['name']==self.selector.get()),None)
    def refresh_library(self):
        self.library.delete(0,'end');self.filtered=[]
        if self.data is None:return
        q=self.query.get().casefold().strip()
        for t in self.data['tracks']:
            if not matches_library_query(t, q):continue
            self.filtered.append(t['id'])
            self.library.insert('end',f"{t.get('title',t['path'])} — {t.get('artist','')} [{t['path']}]")
    def refresh_playlist(self):
        self.plist.delete(0,'end')
        pl=self.current_pl()
        if pl is None:return
        lookup={t['id']:t for t in self.data['tracks']}
        for i,tid in enumerate(pl['track_ids']):
            t=lookup[tid];self.plist.insert('end',f"{i+1:>3}. {t.get('title',t['path'])} — {t.get('artist','')}")
    def add_selected(self):
        pl=self.current_pl();sel=self.library.curselection()
        if pl is None or not sel:return
        add(pl,self.filtered[sel[0]],self.data['tracks']);self.changed=True;self.refresh_playlist()
        self.plist.selection_set('end');self.plist.see('end')
    def remove_selected(self):
        pl=self.current_pl();sel=self.plist.curselection()
        if pl is None or not sel:return
        remove(pl,sel[0]);self.changed=True;self.refresh_playlist()
    def shift(self,delta):
        pl=self.current_pl();sel=self.plist.curselection()
        if pl is None or not sel:return
        i=sel[0]
        if move(pl,i,delta):
            self.changed=True;self.refresh_playlist();self.plist.selection_set(i+delta);self.plist.see(i+delta)
    def choose_output(self,ext):
        p=filedialog.asksaveasfilename(defaultextension=ext,filetypes=[(ext+' file','*'+ext)])
        if not p:return None
        validate_output(p)
        if self.source and os.path.normcase(os.path.abspath(p))==os.path.normcase(os.path.abspath(self.source)):
            raise PlaylistError('Refusing to overwrite original metadata import; use a new filename')
        exists=Path(p).exists()
        if exists and not messagebox.askyesno('Replace output?','Output exists. Replace this explicitly chosen file atomically?'):
            return None
        return Path(p),exists
    def save_file(self):
        if self.data is None:return
        try:
            choice=self.choose_output('.json')
            if choice is None:return
            p,replace_existing=choice
            payload=encode(self.data);atomic_write(p,payload,replace_existing)
            self.changed=False;self.status.set('Saved new metadata JSON: '+p.name+' (not sent to phone)')
        except Exception as e:messagebox.showerror('Save failed',str(e))
    def export_m3u8(self):
        pl=self.current_pl()
        if pl is None:return
        try:
            payload=m3u8(self.data,pl['name'])
            choice=self.choose_output('.m3u8')
            if choice is None:return
            p,replace_existing=choice
            atomic_write(p,payload.encode('utf-8'),replace_existing)
            self.status.set('Exported playlist file: '+p.name+' (player compatibility unverified)')
        except Exception as e:messagebox.showerror('Export failed',str(e))

if __name__=='__main__':App().mainloop()
