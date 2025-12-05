from __future__ import annotations

import datetime
import difflib
import logging
import re
import time
from enum import Flag, auto
from pathlib import Path

import networkx as nx
import setools
from libmata import alphabets as mata_alph
from libmata.nfa import nfa as mata_nfa

from selinuxtool.android.label import EdgeType

from .file_contexts import FileContext
from .permmap import AndroidPermissionMap

_logger = logging.getLogger('SELinuxTool')
_rlogger = logging.getLogger('SELinuxTool:r')

_ascii = {chr(i): i for i in range(32, 127)}
_ascii_alphabet = mata_alph.OnTheFlyAlphabet.from_symbol_map(_ascii)


class SecurityLvl(Flag):
    NONE = 0
    UNTRUSTED = auto()
    TRUSTED = auto()
    CRITICAL = auto()


class Policy:
    STR_HEADERS = '{: <35}   {: <25}   {: <4}   {: <5}   {: <6}   {: <4}   {: <6}   {}'.format(
        'Name', 'Version', 'FC', 'Nodes', 'Edges', 'sN', 'sE', 'Load time (s)'
    )

    def __init__(self, path: Path, permmapfile: str | Path | None = None) -> None:
        self._path = path
        self._permmap = AndroidPermissionMap(permmapfile)
        self._sepolicy: setools.SELinuxPolicy
        self._file_contexts: dict[str, FileContext]
        self._missing_ctx: set[str] = set()
        self._properties: dict[str, str] = {}
        self._graph = nx.DiGraph()
        self._simple_graph = self._graph

    def __str__(self) -> str:
        try:
            return (
                f'{self.name: <35}   {self.version: <25}   {len(self.file_contexts): <4}   '
                f'{len(self._graph.nodes): <5}   {len(self._graph.edges): <6}   '
                f'{len(self._simple_graph.nodes): <4}   {len(self._simple_graph.edges): <6}   '
                f'{self._load_time:10.4f}'
            )
        except AttributeError:
            return f'{self.name} (unloaded)'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Policy):
            return NotImplemented
        return self.version_incr == other.version_incr

    def __lt__(self, other: Policy) -> bool:
        return self.version_incr < other.version_incr

    @property
    def path(self) -> Path:
        return self._path

    @property
    def sepolicy(self) -> setools.SELinuxPolicy:
        return self._sepolicy

    @property
    def file_contexts(self) -> dict[str, FileContext]:
        return self._file_contexts

    # @property
    # def missing_contexts()

    @property
    def perm_map(self) -> AndroidPermissionMap:
        return self._permmap

    @property
    def graph_debug_str(self) -> str:
        return f'[N {len(self._graph.nodes())}] [E {len(self._graph.edges())}]'

    @property
    def simple_graph_debug_str(self) -> str:
        return f'[N {len(self._simple_graph.nodes())}] [E {len(self._simple_graph.edges())}]'

    @property
    def simple_graph(self) -> nx.DiGraph:
        return self._simple_graph

    @property
    def name(self) -> str:
        return self._path.name

    @property
    def version(self) -> str:
        return f'v{self.version_major}.{self.version_incr} ({self.version_patch})'

    @property
    def version_major(self) -> int:
        return int(self._properties['ro.build.version.release'])

    @property
    def version_incr(self) -> int:
        try:
            return int(self._properties['ro.build.version.incremental'])
        except ValueError:
            _logger.warning(
                'No simple incremental version: ' + self._properties['ro.build.version.incremental']
            )
            return 0

    @property
    def version_patch(self) -> datetime.date:
        date_str = self._properties['ro.build.version.security_patch']
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

    @property
    def untrusted_labels(self) -> list[str]:
        untrusted = [
            n
            for n, d in self._graph.nodes(data=True)
            if SecurityLvl.UNTRUSTED in d['security_level']
        ]
        return untrusted

    @property
    def trusted_labels(self) -> list[str]:
        trusted = [
            n for n, d in self._graph.nodes(data=True) if SecurityLvl.TRUSTED in d['security_level']
        ]
        return trusted

    @property
    def critical_labels(self) -> list[str]:
        critical = [
            n
            for n, d in self._graph.nodes(data=True)
            if SecurityLvl.CRITICAL in d['security_level']
        ]
        return critical

    def load_policy(self, load: bool, save: bool, count: int) -> None:
        init_time = time.time()
        if not self._path.exists() or self._path == Path(''):
            _logger.fatal(f'The specified policy ({self._path}) was not found.')
            exit()

        _logger.info(f'Loading policy #{count + 1} ({self._path.name}).')
        self._load_properties()
        self._sepolicy = setools.SELinuxPolicy(str(self._path / 'precompiled_sepolicy'))
        self._load_context(load, save)
        self._load_graph(False, False)  # Seems to be more effective
        self._update_security_labels()
        self._load_time = time.time() - init_time
        _logger.info(f'Loaded policy #{count + 1} in {self._load_time}.')

    def _load_properties(self) -> None:
        with open(self._path / 'build.prop') as prop_file:
            for line_no, line in enumerate(prop_file):
                # Ignore comments and blank lines
                if re.match(r'^(\s*#)|(\s*$)', line):
                    continue

                match = re.match(r'^\s*([-_.a-zA-Z0-9]+)\s*=\s*([^#]*)\n', line)

                if not match:
                    _logger.warning(f'Unhandled property at line {line_no}.')
                    continue

                prop, value = match.groups()
                self._properties[prop] = value

        _logger.info(f'Android version {self.version}.')

    def _load_context(self, load: bool, save: bool) -> None:
        db_exists = (self._path / 'db' / 'file_contexts.db').exists()
        if load and db_exists:
            self._file_contexts = FileContext.load(self._path)
        else:
            self._file_contexts = FileContext.from_files(
                [self._path / 'plat_file_contexts', self._path / 'vendor_file_contexts']
            )

        if save or (load and not db_exists):
            FileContext.save(self._file_contexts, self._path)

    def _load_graph(self, load: bool, save: bool) -> None:
        def attr_to_str(attr: EdgeType | str | bool) -> str:
            if isinstance(attr, EdgeType):
                return attr.name or ''
            return str(attr)

        pattern = re.compile(r"""(?x)
                             (?P<type>(READ|WRITE|UNKN|ADDL)) |
                             (?P<set>{.*}) |
                             (?P<tuple>\(.*\)) |
                             (?P<string>.*)
                             """)

        def str_to_attr(flat_str: str) -> EdgeType | str | set[str] | tuple[str]:
            if flat_str == '_networkx_list_start':
                return flat_str

            mo = pattern.fullmatch(flat_str)
            if not mo:
                raise ValueError
            match mo.lastgroup:
                case 'type':
                    return EdgeType[flat_str]
                case 'set':
                    return set(re.findall(r"'(.*?)'", flat_str))
                case 'tuple':
                    return tuple(re.findall(r"'(.*?)'", flat_str))
                case 'str':
                    return flat_str
                case _:
                    raise ValueError

        init_time = time.time()
        graph_exists = (self._path / 'db' / 'graph.gml').exists()
        if load and graph_exists:
            self._graph = nx.read_gml(self.path / 'db' / 'graph.gml', destringizer=str_to_attr)
            self._simple_graph = nx.read_gml(
                self.path / 'db' / 'simple.gml', destringizer=str_to_attr
            )
        else:
            self._build_graph()
            self._build_simple_graph()

        load_time = time.time() - init_time
        _logger.info(
            f'Loaded graph in {load_time:.4f} {self.graph_debug_str}\t{self.simple_graph_debug_str}'
        )

        if save or (load and not graph_exists):
            nx.write_gml(self._graph, self._path / 'db' / 'graph.gml', attr_to_str)
            nx.write_gml(self._simple_graph, self._path / 'db' / 'simple.gml', attr_to_str)

    def _build_graph(self) -> None:
        def add_edge(source: str, target: str, type: EdgeType, perms: list[str]) -> None:
            if self._graph.has_edge(source, target):
                # TODO: maybe should move set to class
                self._graph.edges[source, target]['perms'] |= set(perms)
                self._graph.edges[source, target]['type'] |= type
            else:
                self._graph.add_edge(source, target, type=type, perms=set(perms))

        def add_subj_node(label: str, transition: tuple[str, str]) -> None:
            if self._graph.has_node(label):
                if self._graph.nodes[label]['is_subject']:
                    self._graph.nodes[label]['transitions'].append(transition)
                else:
                    self._graph.nodes[label]['is_subject'] = True
                    self._graph.nodes[label]['transitions'] = [transition]
            else:
                self._graph.add_node(label, is_subject=True, transitions=[transition])

        for terule in self._sepolicy.terules():
            if isinstance(terule, setools.policyrep.AVRule):
                # TODO: should also handle not allows?
                if terule.ruletype == setools.policyrep.TERuletype.allow:
                    u_label = str(terule.source)
                    v_label = str(terule.target)

                    rule_if = self._permmap.rule_infoflow(terule)

                    if rule_if.read_perms:
                        add_edge(v_label, u_label, EdgeType.READ, rule_if.read_perms)

                    if rule_if.write_perms:
                        add_edge(u_label, v_label, EdgeType.WRITE, rule_if.write_perms)

                    if rule_if.unknown_perms:
                        add_edge(v_label, u_label, EdgeType.UNKN, rule_if.unknown_perms)
                        add_edge(u_label, v_label, EdgeType.UNKN, rule_if.unknown_perms)
        nx.set_node_attributes(self._graph, False, 'is_object')
        nx.set_node_attributes(self._graph, False, 'is_subject')
        _logger.debug(f'Processed allow rules. {self.graph_debug_str}')

        # Handling file contexts
        for ctx, _ in self._file_contexts.items():
            self._graph.add_node(ctx, is_object=True)
        _logger.debug(f'Processed file contexts. {self.graph_debug_str}')

        # Handling subject type transitions
        for terule in list(self._sepolicy.terules()):
            if (
                isinstance(terule, setools.policyrep.TERule)
                and terule.ruletype == setools.policyrep.TERuletype.type_transition
            ):
                # TODO: check
                if not self._graph.nodes[terule.target]['is_object']:
                    self._missing_ctx.add(str(terule.target))

                u_label = str(terule.source)
                v_label = str(terule.default)  # target is the object used for the transition
                fc_label = str(terule.target)

                # TODO: check if we need the file qualifier (terule.filename)
                add_subj_node(v_label, (u_label, fc_label))
        _logger.debug(f'Processed type transitions. {self.graph_debug_str}')
        _logger.warning(f'Missing {len(self._missing_ctx)} contexts in type transitions.')

    def _build_simple_graph(self) -> None:
        graph: nx.DiGraph = self._graph.copy()
        nodes = [(n, graph.nodes[n]) for (n, deg) in sorted(graph.degree, key=lambda x: x[1])]
        for progress, (node, node_data) in enumerate(nodes):
            _rlogger.debug(f'Simplifying graph: {progress + 1} / {len(nodes)}')
            if node_data['is_object']:
                continue

            for in_node, _, in_edge in graph.in_edges(node, data=True):
                if not in_node == node:
                    for _, out_node, out_edge in graph.out_edges(node, data=True):
                        if not out_node == node:
                            if not graph.has_edge(in_node, out_node):
                                omitted_nodes = [node]
                                # TODO: aggiungere permessi in else
                                if in_edge['type'] == EdgeType.ADDL:
                                    omitted_nodes += in_edge['omitted']
                                if out_edge['type'] == EdgeType.ADDL:
                                    omitted_nodes += out_edge['omitted']

                                graph.add_edge(
                                    in_node, out_node, type=EdgeType.ADDL, omitted=omitted_nodes
                                )
            graph.remove_node(node)
        self._simple_graph = graph
        _logger.debug('')
        _logger.info(f'Simplified graph to only object nodes. {self.simple_graph_debug_str}')

    def _update_security_labels(self) -> None:
        UNTRUSTED_KW = ['isolate', 'untrust', 'danger', 'user', 'usr', 'debug', 'network']
        TRUSTED_KW = ['trust', 'secur']
        CRITICAL_KW = ['system', 'pol', 'critic', 'manager']

        self._security_lvs: dict[SecurityLvl, list[str]] = {}
        for node in self._graph:
            level = SecurityLvl.NONE
            if any(kw in node for kw in UNTRUSTED_KW):
                level |= SecurityLvl.UNTRUSTED
            if any(kw in node for kw in TRUSTED_KW) and 'untrust' not in node:
                level |= SecurityLvl.TRUSTED
            if any(kw in node for kw in CRITICAL_KW):
                level |= SecurityLvl.CRITICAL

            if level not in self._security_lvs:
                self._security_lvs[level] = []
            self._security_lvs[level].append(node)
            self._graph.nodes[node]['security_level'] = level

    # File contexts diffs
    def fc_diff(self, other: Policy) -> tuple[list[str], int, int]:
        def str_filter(line: str) -> str:
            return re.sub(r'\s+', ' ', line.strip())

        with (
            open(self._path / 'plat_file_contexts', 'r') as ctx_L,
            open(other._path / 'plat_file_contexts', 'r') as ctx_R,
        ):
            lines_L = [str_filter(line) for line in ctx_L]
            lines_R = [str_filter(line) for line in ctx_R]
            delta = [
                line.rstrip()
                for line in difflib.ndiff(lines_L, lines_R)
                if not line.startswith('  ')
            ]
            delta_del = [line for line in delta if line.startswith('-')]
            delta_add = [line for line in delta if line.startswith('+')]

        return (delta, len(delta_del), len(delta_add))

    def type_diff(self, other: Policy) -> tuple[set[str], set[str], set[str], set[str]]:
        self_nodes = set(self._graph.nodes)
        self_edges = set(self._graph.edges)
        other_nodes = set(other._graph.nodes)
        other_edges = set(other._graph.edges)

        nodes_only_self = self_nodes.difference(other_nodes)
        nodes_only_other = other_nodes.difference(self_nodes)
        edges_only_self = self_edges.difference(other_edges)
        edges_only_other = other_edges.difference(self_edges)

        return (nodes_only_self, nodes_only_other, edges_only_self, edges_only_other)

    def security_lvs_diff(self, other: Policy) -> tuple[set[str], mata_nfa.Nfa]:
        initial_self = set()
        initial_other = set()

        for source in other.untrusted_labels:
            if source in self._graph:
                if any(
                    target in self._graph and nx.has_path(self._graph, source, target)
                    for target in other.critical_labels
                ):
                    initial_self.add(source)

            if any(nx.has_path(other._graph, source, target) for target in other.critical_labels):
                initial_other.add(source)

        init_fc_self_blu = mata_nfa.Nfa()  # empty lang
        init_fc_other_blu = mata_nfa.Nfa()

        for label in initial_self:
            if label in self._file_contexts:
                init_fc_self_blu = mata_nfa.union(init_fc_self_blu, self._file_contexts[label].nfa)

        for label in initial_other:
            if label in other._file_contexts:
                init_fc_other_blu = mata_nfa.union(
                    init_fc_other_blu, other._file_contexts[label].nfa
                )

        other._init_fc_blu = init_fc_other_blu  # TODO: should change

        minimal_nfa = mata_nfa.minimize(
            mata_nfa.intersection(
                init_fc_other_blu, mata_nfa.complement(init_fc_self_blu, _ascii_alphabet)
            )
        )

        return (initial_other - initial_self, minimal_nfa)
