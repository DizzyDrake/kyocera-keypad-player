"""Headless unit test of the real IntegratedApp.open_saved_plan method."""
import copy, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from bridge import phone_to_pc, plan
from integrated_app import IntegratedApp

class FakeEditor:
    open_saved_plan=IntegratedApp.open_saved_plan
    def __init__(self, phone):
        self.phone_snapshot=phone
        self.data=phone_to_pc(phone)
        self.source='old-editor.json'
        self.changed=False
        self._undo=['prior']
        self.status=type('Status',(),{'set':lambda self,x:setattr(self,'value',x)})()
        self.calls=[]
    def confirm_discard(self): return True
    def update_selector(self,x): self.calls.append(('selector',x))
    def refresh_library(self): self.calls.append('library')
    def refresh_playlist(self): self.calls.append('playlist')

class Tests(unittest.TestCase):
    def setUp(self):
        self.phone=json.loads((Path(__file__).parents[1]/'sample/dev8_fictional_phone_export.json').read_text())
    def test_recover_and_preserve_phone(self):
        editor=FakeEditor(self.phone)
        edited=phone_to_pc(self.phone)
        edited['playlists'][0]['name']='Recovered'
        saved=plan(self.phone,edited)
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'saved-plan.json';f.write_text(json.dumps(saved))
            with patch('integrated_app.filedialog.askopenfilename',return_value=str(f)):
                editor.open_saved_plan()
        self.assertEqual(editor.data,edited)
        self.assertEqual(editor.phone_snapshot,self.phone)
        self.assertTrue(editor.changed)
        self.assertIsNone(editor.source)
        self.assertEqual(editor._undo,[])
    def test_stale_plan_does_not_mutate_editor(self):
        editor=FakeEditor(self.phone)
        edited=phone_to_pc(self.phone)
        saved=plan(self.phone,edited)
        editor.phone_snapshot=copy.deepcopy(self.phone)
        editor.phone_snapshot['snapshot_id']='later'
        prior=copy.deepcopy(editor.data)
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'saved-plan.json';f.write_text(json.dumps(saved))
            with patch('integrated_app.filedialog.askopenfilename',return_value=str(f)),patch('integrated_app.messagebox.showerror') as error:
                editor.open_saved_plan()
                error.assert_called_once()
        self.assertEqual(editor.data,prior)
        self.assertEqual(editor.source,'old-editor.json')
    def test_missing_snapshot_requires_snapshot(self):
        editor=FakeEditor(self.phone);editor.phone_snapshot=None
        with patch('integrated_app.messagebox.showinfo') as info:
            editor.open_saved_plan();info.assert_called_once()
        self.assertEqual(editor.source,'old-editor.json')
if __name__=='__main__':unittest.main()
