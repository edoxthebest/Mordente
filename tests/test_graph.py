import unittest

import networkx as nx

from selinuxtool.android.graph import InfoFlowGraph


class TestGraph(unittest.TestCase):
    def setUp(self) -> None:
        stub_graph = nx.MultiDiGraph()
        left_edges = [  # D -> ^C -> B <- A <-> ^E
            ('A', 'B'),
            ('A', 'E'),
            ('C', 'C'),
            ('C', 'B'),
            ('D', 'C'),
            ('E', 'A'),
            ('E', 'E'),
        ]
        right_edges = [(y, x) for (x, y) in left_edges]  # D <- ^C <- B -> A <-> ^E
        stub_graph.add_edges_from(left_edges, direction='left')
        stub_graph.add_edges_from(right_edges, direction='right')
        self.graph = InfoFlowGraph(None, None)
        self.graph._graph = stub_graph

    def test_eventually_reach(self) -> None:
        self.assertEqual(self.graph.eventually_reach(['A'], 'left'), {'A', 'E'})
        self.assertEqual(self.graph.eventually_reach(['B'], 'left'), {'A', 'C', 'D', 'E'})
        self.assertEqual(self.graph.eventually_reach(['C'], 'left'), {'C', 'D'})
        self.assertEqual(self.graph.eventually_reach(['D'], 'left'), set())
        self.assertEqual(self.graph.eventually_reach(['E'], 'left'), {'A', 'E'})

        self.assertEqual(self.graph.eventually_reach(['A'], 'right'), {'A', 'B', 'E'})
        self.assertEqual(self.graph.eventually_reach(['B'], 'right'), set())
        self.assertEqual(self.graph.eventually_reach(['C'], 'right'), {'B', 'C'})
        self.assertEqual(self.graph.eventually_reach(['D'], 'right'), {'B', 'C'})
        self.assertEqual(self.graph.eventually_reach(['E'], 'right'), {'A', 'B', 'E'})

    def test_eventually_reached_by(self) -> None:
        self.assertEqual(self.graph.eventually_reached_by(['A'], 'right'), {'A', 'E'})
        self.assertEqual(self.graph.eventually_reached_by(['B'], 'right'), {'A', 'C', 'D', 'E'})
        self.assertEqual(self.graph.eventually_reached_by(['C'], 'right'), {'C', 'D'})
        self.assertEqual(self.graph.eventually_reached_by(['D'], 'right'), set())
        self.assertEqual(self.graph.eventually_reached_by(['E'], 'right'), {'A', 'E'})

        self.assertEqual(self.graph.eventually_reached_by(['A'], 'left'), {'A', 'B', 'E'})
        self.assertEqual(self.graph.eventually_reached_by(['B'], 'left'), set())
        self.assertEqual(self.graph.eventually_reached_by(['C'], 'left'), {'B', 'C'})
        self.assertEqual(self.graph.eventually_reached_by(['D'], 'left'), {'B', 'C'})
        self.assertEqual(self.graph.eventually_reached_by(['E'], 'left'), {'A', 'B', 'E'})
