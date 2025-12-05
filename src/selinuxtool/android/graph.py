import logging
import time

import networkx as nx
from libmata import alphabets as mata_alph
from libmata.nfa import nfa as mata_nfa

from selinuxtool.android.policy import Policy, SecurityLvl

_logger = logging.getLogger('SELinuxTool')
_rlogger = logging.getLogger('SELinuxTool:r')

# TODO: move to util
_ascii = {chr(i): i for i in range(32, 127)}
_ascii_alphabet = mata_alph.OnTheFlyAlphabet.from_symbol_map(_ascii)


class InfoFlowGraph:
    def __init__(self, left: Policy, right: Policy) -> None:
        self._left = left
        self._right = right
        self._graph = nx.MultiDiGraph()  # TODO: this should prolly build the graph

    @property
    def graph(self) -> nx.MultiDiGraph:
        return self._graph

    @property
    def labels(self) -> set[tuple[str, str]]:
        return set(self._graph.nodes)

    @property
    def graph_debug_str(self) -> str:
        return f'[N {len(self._graph.nodes())}] [E {len(self._graph.edges())}]'

    def build_graph(self) -> None:
        init_time = time.time()

        left_g = self._left.simple_graph
        right_g = self._right.simple_graph

        for progress, data in enumerate(left_g.nodes.items()):
            _rlogger.info(f'Constructing InfoFlowGraph... {progress + 1} / {len(left_g.nodes)}')
            left_label, _ = data
            left_label_fc = self._left.file_contexts[left_label].nfa
            for right_label, _ in right_g.nodes.items():
                right_label_fc = self._right.file_contexts[right_label].nfa
                lr_fc_inter = mata_nfa.intersection(left_label_fc, right_label_fc)

                if not lr_fc_inter.is_lang_empty():
                    self._graph.add_node((left_label, right_label))
                #     if left_label != right_label:
                #         _logger.debug(f'L ({left_label}) - R ({right_label}) [NOT EQUAL]')
                # elif left_label == right_label:
                #     _logger.debug(f'L ({left_label}) - R ({right_label}) [EMPTY INTER]')

        for left_label_1, right_label_1 in self._graph.nodes:
            for left_label_2, right_label_2 in self._graph.nodes:
                if left_g.has_edge(left_label_1, left_label_2):
                    self._graph.add_edge(
                        (left_label_1, right_label_1),
                        (left_label_2, right_label_2),
                        direction='left',
                    )
                if right_g.has_edge(right_label_1, right_label_2):
                    self._graph.add_edge(
                        (left_label_1, right_label_1),
                        (left_label_2, right_label_2),
                        direction='right',
                    )
        self._built_time = time.time() - init_time
        _logger.info(f'Built InfoFlowGraph {self.graph_debug_str} in {self._built_time}.')

    def has_path(self, source: str, target: str, kind: int = 0) -> bool:
        # kind 0 = left, kind 1 = right
        def left_weighted(source: tuple, target: tuple, edge_attrs: dict) -> int:
            if any(edge['direction'] == 'left' for _, edge in edge_attrs.items()):
                return 0
            return 1

        try:
            nx.shortest_path(self._graph, source, target, weight=left_weighted)
        except nx.NetworkXNoPath:
            return False

        return nx.shortest_path_length(self._graph, source, target, weight=left_weighted) == 0

    def security_lvs_diff(self) -> None:
        untrusted_right_in_left = [
            (x, y)
            for (x, y) in self._graph.nodes()
            if SecurityLvl.UNTRUSTED in self._right._graph.nodes[y]['security_level']
        ]

        critical_right_in_left = [
            (x, y)
            for (x, y) in self._graph.nodes()
            if SecurityLvl.CRITICAL in self._right._graph.nodes[y]['security_level']
        ]

        initial_right_in_left = set()
        for source in untrusted_right_in_left:
            if any(self.has_path(source, target) for target in critical_right_in_left):
                initial_right_in_left.add(source)

        init_fc_left = mata_nfa.Nfa()  # empty lang
        fc_untrust_right = mata_nfa.Nfa()
        for label, _ in initial_right_in_left:
            if label in self._left._file_contexts:
                init_fc_left = mata_nfa.union(init_fc_left, self._left._file_contexts[label].nfa)
        for label in self._right.untrusted_labels:
            if label in self._right._file_contexts:
                fc_untrust_right = mata_nfa.union(
                    fc_untrust_right, self._right._file_contexts[label].nfa
                )

        init_fc_left = mata_nfa.intersection(init_fc_left, fc_untrust_right)
        init_fc_right = self._right._init_fc_blu

        minimal_nfa = mata_nfa.minimize(
            mata_nfa.intersection(init_fc_right, mata_nfa.complement(init_fc_left, _ascii_alphabet))
        )
        return minimal_nfa

    def eventually_reachable(
        self, nodes: set[tuple[str, str]], direction: str = 'left', type: str = 'in'
    ) -> set[tuple[str, str]]:
        # Set function to use based on the given type.
        if type == 'in':
            in_out_edges = self._graph.in_edges
        elif type == 'out':
            in_out_edges = self._graph.out_edges
        else:
            raise ValueError('Invalid type (only in/out).')

        reachable_nodes = set()
        nodes_to_process = list(nodes)

        while nodes_to_process:
            for source, target, edge in in_out_edges(nodes_to_process.pop(), data=True):
                candidate = source if type == 'in' else target

                if edge['direction'] == direction and candidate not in reachable_nodes:
                    reachable_nodes.add(candidate)
                    if candidate not in nodes:
                        nodes_to_process.append(candidate)

        return reachable_nodes

    def eventually_reach(
        self, nodes: set[tuple[str, str]], direction: str = 'left'
    ) -> set[tuple[str, str]]:
        return self.eventually_reachable(nodes, direction, type='in')

    def eventually_reached_by(
        self, nodes: set[tuple[str, str]], direction: str = 'left'
    ) -> set[tuple[str, str]]:
        return self.eventually_reachable(nodes, direction, type='out')


# nodi che soddifano \phi
## insieme soddisfa diamond {}
#  coda {nodi che soddisfano \phi}
#
# finchè coda non vuota
#       prendi nodo da coda
#       calcoli predecessori del nodo
#       aggiungi all'insieme
#       se viene aggiunto, lo metti in coda unless soddisfa \phi
