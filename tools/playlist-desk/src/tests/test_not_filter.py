import unittest
from app import matches_library_query

TRACKS = [
    {'title':'Blue Jazz Live','artist':'A','album':'Concert','genre':'Jazz','path':'a.mp3'},
    {'title':'Blue Jazz Studio','artist':'B','album':'Record','genre':'Jazz','path':'b.mp3'},
    {'title':'Christmas Carol','artist':'C','album':'Holiday','genre':'Folk','path':'c.mp3'},
    {'title':'Jazz Remix','artist':'D','album':'Record','genre':'Jazz','path':'d.mp3'},
]
class NotFilterTests(unittest.TestCase):
    def ids(self, q):
        return [i for i,t in enumerate(TRACKS) if matches_library_query(t,q)]
    def test_empty(self): self.assertEqual(self.ids(''), [0,1,2,3])
    def test_old_phrase(self): self.assertEqual(self.ids('blue jazz'), [0,1])
    def test_positive(self): self.assertEqual(self.ids('jazz'), [0,1,3])
    def test_exclusion(self): self.assertEqual(self.ids('jazz NOT live'), [1,3])
    def test_leading(self): self.assertEqual(self.ids('NOT christmas'), [0,1,3])
    def test_multiple(self): self.assertEqual(self.ids('jazz NOT live NOT remix'), [1])
    def test_case(self): self.assertEqual(self.ids('JaZz nOt LiVe'), [1,3])
    def test_whole_word_operator(self): self.assertEqual(self.ids('NOTebook'), [])
    def test_trailing_operator_literal(self): self.assertEqual(self.ids('jazz NOT'), [])
    def test_metadata_fields(self): self.assertEqual(self.ids('record NOT remix'), [1])
if __name__=='__main__': unittest.main()
