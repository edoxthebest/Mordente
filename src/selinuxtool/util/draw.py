import networkx as nx
import time
from pyvis.network import Network
from selinuxtool.android.label import InfoFlowEdge, EdgeType, Label, LabelType


def make_drawable(graph: nx.MultiDiGraph):
    drawable_graph = nx.MultiDiGraph()
    drawable_nodes = []
    drawable_edges = []

    for node, data in graph.nodes(data=True):
        label: Label = data['data']

        match label.type:
            case LabelType.UNKNOWN:
                shape = 'dot'
                title = ''
            case LabelType.OBJECT:
                shape = 'diamond'
                title = str(label.fc)
            case LabelType.SUBJECT:
                shape = 'triangle'
                title = str(label.subjects)
            case LabelType.BOTH:
                shape = 'star'
                title = 'TODO'

        drawable_nodes.append((node, {'shape': shape, 'title': title}))

    for u, v, data in graph.edges(data=True):
        edge: InfoFlowEdge = data['data']

        match edge.type:
            case EdgeType.READ:
                color = 'red'

            case EdgeType.WRITE:
                color = 'blue'

            case EdgeType.BOTH:
                color = 'purple'

            case EdgeType.UNKN:
                color = 'black'

            case EdgeType.ADDL:
                color = 'green'

            case _:
                color = 'purple'

        title = str(edge.perms)

        drawable_edges.append((u, v, {'color': color, 'title': title}))

    drawable_graph.add_nodes_from(drawable_nodes)
    drawable_graph.add_edges_from(drawable_edges)

    return drawable_graph


def draw_graph(graph: nx.MultiDiGraph, title='test'):
    graph = make_drawable(graph)
    net = Network(notebook=False, directed=True)
    net.from_nx(graph)
    net.show_buttons(filter_=['physics'])
    net.show('out/' + title + '.html', notebook=False)


def get_missing_edges(graph: nx.MultiDiGraph):
    for u, v, attrs in graph.edges(data=True):
        if 'missing' in attrs.keys():
            yield (u, v, attrs)


def draw_missing_edges(graph: nx.MultiDiGraph):
    missing_edges_G = nx.MultiDiGraph()
    missing_edges_G.add_edges_from(get_missing_edges(graph))
    draw_graph(missing_edges_G)


def draw_automata(nfa, title='automata' + str(int(time.time()))):
    graph = nx.DiGraph()
    for trans in nfa.iterate():
        if graph.has_edge(trans.source, trans.target):
            graph[trans.source][trans.target]['title'] += '|' + chr(trans.symbol)
        else:
            graph.add_edge(trans.source, trans.target, title=chr(trans.symbol))

    net = Network(notebook=False, directed=True)
    net.from_nx(graph)
    net.show('out/' + title + '.html', notebook=False)
