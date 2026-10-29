"""Source-level regression checks only; not an Android runtime or E4831 test."""
from pathlib import Path
import unittest
import sys

ACTIVITY=Path(sys.argv[1]) if len(sys.argv)>1 else Path('src/app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java')

class PromptContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=ACTIVITY.read_text()
        cls.prompt=source.split('private void prompt(',1)[1].split('private void message(',1)[0]
        cls.all_source=source
    def test_ime_done_is_explicit(self):
        self.assertIn('setImeOptions(EditorInfo.IME_ACTION_DONE)',self.prompt)
        self.assertIn('setOnEditorActionListener',self.prompt)
        self.assertIn('EditorInfo.IME_ACTION_DONE',self.prompt)
    def test_physical_center_and_enter(self):
        for token in ['KEYCODE_DPAD_CENTER','KEYCODE_ENTER','KEYCODE_NUMPAD_ENTER','save.performClick()']:
            self.assertIn(token,self.prompt)
    def test_physical_navigation_to_visible_buttons(self):
        for token in ['KEYCODE_DPAD_DOWN','save.requestFocus()','KEYCODE_DPAD_UP','cancel.requestFocus()']:
            self.assertIn(token,self.prompt)
    def test_validation_does_not_auto_dismiss(self):
        self.assertIn('.setPositiveButton("Save",null)',self.prompt)
        self.assertIn('save.setOnClickListener',self.prompt)
        self.assertIn('input.setError("Name cannot be empty")',self.prompt)
        self.assertIn('if(val.isEmpty())',self.prompt)
    def test_save_and_cancel_not_automatic(self):
        self.assertIn('onSave.accept(val)',self.prompt)
        self.assertIn('save.setEnabled(false)',self.prompt)
        self.assertIn('dialog.dismiss()',self.prompt)
        self.assertIn('.setNegativeButton("Cancel"',self.prompt)
        self.assertIn('event.getAction()==KeyEvent.ACTION_UP',self.prompt)
    def test_other_flows_untouched(self):
        self.assertIn('item("+ Create playlist",()->prompt(',self.all_source)
        self.assertIn('item("Rename playlist",()->prompt(',self.all_source)
        self.assertIn('item("Filter by title / artist / album / folder",()->prompt(',self.all_source)

if __name__=='__main__':
    unittest.main(argv=[sys.argv[0]],verbosity=2)
