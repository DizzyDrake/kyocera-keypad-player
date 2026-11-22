import unittest
from two_pane_actions import insert_selected, remove_selected_indices, move_selected_block

class TwoPanePureTests(unittest.TestCase):
    def test_add_multiple_in_order(self):
        pl={'track_ids':['a','d']}
        self.assertEqual(insert_selected(pl,['b','c'],1),2)
        self.assertEqual(pl['track_ids'],['a','b','c','d'])
    def test_append_multiple_skips_duplicates_for_bridge(self):
        pl={'track_ids':['a']}
        insert_selected(pl,['a','b'])
        self.assertEqual(pl['track_ids'],['a','b'])
    def test_remove_selected_indices_descending(self):
        pl={'track_ids':['a','b','c','d','e']}
        self.assertEqual(remove_selected_indices(pl,[3,1,1,99]),['b','d'])
        self.assertEqual(pl['track_ids'],['a','c','e'])
    def test_reorder_disjoint_group(self):
        pl={'track_ids':['a','b','c','d','e']}
        self.assertEqual(move_selected_block(pl,[1,3],5),[3,4])
        self.assertEqual(pl['track_ids'],['a','c','e','b','d'])
    def test_reorder_group_to_front(self):
        pl={'track_ids':['a','b','c','d','e']}
        self.assertEqual(move_selected_block(pl,[2,3],0),[0,1])
        self.assertEqual(pl['track_ids'],['c','d','a','b','e'])
    def test_noop_keeps_original(self):
        pl={'track_ids':['a','b','c']}
        self.assertEqual(move_selected_block(pl,[1],2),[])
        self.assertEqual(pl['track_ids'],['a','b','c'])
    def test_reorder_duplicate_occurrences(self):
        pl={'track_ids':['a','a','b']}
        self.assertEqual(move_selected_block(pl,[1],3),[2])
        self.assertEqual(pl['track_ids'],['a','b','a'])
    def test_out_of_bounds_remove_is_ignored(self):
        pl={'track_ids':['a','b']}
        self.assertEqual(remove_selected_indices(pl,[-1,7]),[])
        self.assertEqual(pl['track_ids'],['a','b'])

if __name__=='__main__': unittest.main()
