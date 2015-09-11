import unittest
import pdb
from apriori_based_anon import apriori_based_anon
from RT_ANON import rt_anon
from models.gentree import GenTree
from evaluation import count_query, est_query, get_result_cover, average_relative_error

# Build a GenTree object
ATT_TREE = {}


def init_tree():
    global ATT_TREE
    ATT_TREE = {}
    root = GenTree('*')
    ATT_TREE['*'] = root
    lt = GenTree('A', root)
    ATT_TREE['A'] = lt
    ATT_TREE['a1'] = GenTree('a1', lt, True)
    ATT_TREE['a2'] = GenTree('a2', lt, True)
    rt = GenTree('B', root)
    ATT_TREE['B'] = rt
    ATT_TREE['b1'] = GenTree('b1', rt, True)
    ATT_TREE['b2'] = GenTree('b2', rt, True)


class test_Apriori_based_Anon(unittest.TestCase):
    def test_AA_with_AA_case(self):
        init_tree()
        trans = [['a1', 'b1', 'b2'],
                 ['a2', 'b1'],
                 ['a2', 'b1', 'b2'],
                 ['a1', 'a2', 'b2']]
        _, result = apriori_based_anon(ATT_TREE, trans, 'AA', 2, 2)
        self.assertEqual(result[2], {'a1': 'A', 'a2': 'A'})
        _, result = apriori_based_anon(ATT_TREE, trans, 'DA', 2, 2)
        self.assertEqual(result[2], {'a1': 'A', 'a2': 'A'})

    def test_AA_partition_case1(self):
        init_tree()
        trans = [['a1'],
                 ['a1', 'a2'],
                 ['b1', 'b2'],
                 ['b1', 'b2'],
                 ['a1', 'a2', 'b2'],
                 ['a1', 'a2', 'b2'],
                 ['a1', 'a2', 'b1', 'b2']]
        _, result = apriori_based_anon(ATT_TREE, trans, 'AA', 2, 4)
        # not {'a1': 'A', 'a2': 'A', 'b1': 'B', 'b2': 'B'}
        self.assertEqual(result[2], {'b1': 'B', 'b2': 'B'})
        _, result = apriori_based_anon(ATT_TREE, trans, 'AA', 2, 2)
        self.assertEqual(result[2], {'b1': 'B', 'b2': 'B'})

    def test_DA_partition_case2(self):
        init_tree()
        trans = [['a1'],
                 ['a1', 'a2'],
                 ['b1', 'b2'],
                 ['b1', 'b2'],
                 ['a1', 'a2', 'b2'],
                 ['a1', 'a2', 'b2'],
                 ['a1', 'a2', 'b1', 'b2']]
        _, result = apriori_based_anon(ATT_TREE, trans, 'DA', 2, 4)
        # not {'a1': 'A', 'a2': 'A', 'b1': 'B', 'b2': 'B'}
        self.assertEqual(result[2], {'b1': 'B', 'b2': 'B'})
        _, result = apriori_based_anon(ATT_TREE, trans, 'DA', 2, 2)
        self.assertEqual(result[2], {'b1': 'B', 'b2': 'B'})

    def test_RMR_with_full_threshold(self):
        init_tree()
        att_trees = [ATT_TREE, ATT_TREE]
        data = [['a1', ['a1']],
                ['a1', ['a1', 'a2']],
                ['b1', ['b1', 'b2']],
                ['b2', ['b1', 'b2']],
                ['b1', ['a1', 'a2', 'b2']],
                ['b2', ['a1', 'a2', 'b2']],
                ['a1', ['a1', 'a2', 'b1', 'b2']]]
        _, result = rt_anon(att_trees, data, 'RMR', 2, 2, 1.0)
        self.assertTrue(abs(result[1] - 8 * 0.5 * 100 / 17) <= 0.001)

    def test_RMR_RMT_with_self_case(self):
        init_tree()
        att_trees = [ATT_TREE, ATT_TREE]
        data = [['a1', ['a1', 'b1', 'b2']],
                ['a1', ['a2', 'b1']],
                ['a2', ['a2', 'b1', 'b2']],
                ['a2', ['a1', 'a2', 'b2']]]
        _, result = rt_anon(att_trees, data, 'RMR', 2, 2, 1.0)
        self.assertTrue(abs(result[1] - 0.5 * 5 / 11 * 100) <= 0.001)
        _, result = rt_anon(att_trees, data, 'RMR', 2, 2, 0.1)
        self.assertTrue(abs(result[0] - 0) <= 0.001)
        self.assertTrue(abs(result[1] - 50) <= 0.001)
        _, result = rt_anon(att_trees, data, 'RMT', 2, 2, 1.0)
        self.assertTrue(abs(result[1] - 0.5 * 5 / 11 * 100) <= 0.001)
        _, result = rt_anon(att_trees, data, 'RMT', 2, 2, 0.1)
        self.assertTrue(abs(result[0] - 0) <= 0.001)
        self.assertTrue(abs(result[1] - 50) <= 0.001)

    def test_RMR_with_merge_case(self):
        init_tree()
        att_trees = [ATT_TREE, ATT_TREE]
        data = [['a1', ['a1', 'b1', 'b2']],
                ['a1', ['a2', 'b1']],
                ['a2', ['a2', 'b1', 'b2']],
                ['a2', ['a1', 'a2', 'b2']],
                ['b1', ['a2', 'b1', 'b2']],
                ['b1', ['a1', 'a2', 'b2']],
                ['b2', ['a2', 'b1', 'b2']],
                ['b2', ['a1', 'a2', 'b2']]]
        _, result = rt_anon(att_trees, data, 'RMR', 2, 2, 0.5)
        # print result
        self.assertTrue(abs(result[0] - 50) <= 0.001)
        self.assertTrue(abs(result[1] - 0.5 * 5 / 23 * 100) <= 0.001)

    def test_RMT_with_merge_case(self):
        init_tree()
        att_trees = [ATT_TREE, ATT_TREE]
        data = [['a2', ['a1', 'b1']],
                ['a1', ['a1', 'b1']],
                ['b2', ['a2', 'b2']],
                ['b2', ['a2', 'b2']],
                ['b1', ['a1', 'b1']],
                ['b1', ['a1', 'b1']]]
        _, result = rt_anon(att_trees, data, 'RMT', 2, 2, 0.5)
        self.assertTrue(abs(result[0] - 50) <= 0.001)
        self.assertTrue(abs(result[1] - 0) <= 0.001)
        _, result = rt_anon(att_trees, data, 'RMT', 2, 2, 0.7)
        self.assertTrue(abs(result[0] - 200.0 / 3) <= 0.001)
        self.assertTrue(abs(result[1] - 0) <= 0.001)

    def test_get_result_cover(self):
        init_tree()
        att_trees = [ATT_TREE, ATT_TREE]
        result = [['a1', ['A', 'b1', 'b2']],
                  ['a1', ['A', 'b1']],
                  ['a2', ['A', 'b1', 'b2']],
                  ['a2', ['A', 'b2']]]
        gen_data = get_result_cover(att_trees, result)
        temp = [[{'a1': 1.0}, {'a1': 0.5, 'a2': 0.5, 'b1': 1.0, 'b2': 1.0}],
                [{'a1': 1.0}, {'a1': 0.5, 'a2': 0.5, 'b1': 1.0}],
                [{'a2': 1.0}, {'a1': 0.5, 'a2': 0.5, 'b1': 1.0, 'b2': 1.0}],
                [{'a2': 1.0}, {'a1': 0.5, 'a2': 0.5, 'b2': 1.0}]]
        self.assertEqual(gen_data, temp)

    def test_count_query(self):
        init_tree()
        att_trees = [ATT_TREE, ATT_TREE]
        data = [['a1', ['a1', 'b1', 'b2']],
                ['a1', ['a2', 'b1']],
                ['a2', ['a2', 'b1', 'b2']],
                ['a2', ['a1', 'a2', 'b2']]]
        count = count_query(data, [0, 1], [['a1', 'a2'], [['a2', 'b1'], ['a1', 'b1', 'b2']]])
        self.assertEqual(count, 2)

    def test_est_query(self):
        init_tree()
        att_trees = [ATT_TREE, ATT_TREE]
        result = [['a1', ['A', 'b1', 'b2']],
                  ['a1', ['A', 'b1']],
                  ['a2', ['A', 'b1', 'b2']],
                  ['a2', ['A', 'b2']]]
        gen_data = get_result_cover(att_trees, result)
        est = est_query(gen_data, [0, 1], [['a1', 'a2'], [['a2', 'b1'], ['a1', 'b1', 'b2']]])
        self.assertEqual(est, 2.5)

    def test_are(self):
        init_tree()
        att_trees = [ATT_TREE, ATT_TREE]
        data = [['a1', ['a1', 'b1', 'b2']],
                ['a1', ['a2', 'b1']],
                ['a2', ['a2', 'b1', 'b2']],
                ['a2', ['a1', 'a2', 'b2']]]
        result = [['a1', ['A', 'b1', 'b2']],
                  ['a1', ['A', 'b1']],
                  ['a2', ['A', 'b1', 'b2']],
                  ['a2', ['A', 'b2']]]
        are = average_relative_error(att_trees, data, result, 1, 5)
        # self.assertEqual(are, 0.5)

if __name__ == '__main__':
    unittest.main()
