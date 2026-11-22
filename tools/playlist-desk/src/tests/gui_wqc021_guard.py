from unittest.mock import patch
from integrated_app import IntegratedApp
from tkinter import messagebox

app=IntegratedApp();app.withdraw()
try:
    for invalid in ({'tracks':None},{'tracks':{}},{'tracks':[None]},{'tracks':['bad']},{'tracks':[{'id':'a'},4]}):
        app.data=invalid
        with patch.object(messagebox,'showerror') as error:
            assert app.review_duplicates() is None
            assert error.call_count==1, (invalid,error.call_count)
    print('PASS: five malformed catalog shapes rejected by actual Tk app')
finally:
    app.destroy()
