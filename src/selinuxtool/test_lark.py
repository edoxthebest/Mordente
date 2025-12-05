import logging
from pathlib import Path

from lark import Lark, ast_utils, logger

from selinuxtool.android.graph import InfoFlowGraph
from selinuxtool.android.policy import Policy
from selinuxtool.ifdif.parser import Parser
from selinuxtool.ifdif.solver import Solver

logger.setLevel(logging.DEBUG)

samples = [
    'true',
    'label_5 (X)',
    'true and label_3 (Y)',
    'not label_4 (Z)',
    'ito_1 label_2 (A)',
    'ito_3 not label_6 (T) and true',  # <-- do we need brackets?
    'ito_3 ((not label_6 (T)) and true)',
    '(ito_3 not label_6 (T)) and true',
    'not true and not true',
    'true and not true and true',
]

parser = Parser()

for sample in samples:
    print(sample)
    print(parser.solve(sample))
    print('----')


policyA = Policy(Path('policies/tests/example_policy_1'))
policyB = Policy(Path('policies/tests/example_policy_2'))
policyA.load_policy(False, False, 0)
policyB.load_policy(False, False, 1)
graph = InfoFlowGraph(policyA, policyB)
graph.build_graph()
print(graph.graph_debug_str)

# query = 'not (dia_1 up_1_d and not (up_2_e and dia_2 up_1_d))'
query = 'ito_1 (label_1 (d)) and not (label_2 (e) and ito_2 (label_1 (d)))'
# query = 'dia_1 up_1_d'
ast = parser.solve(query)
print(ast)

solver = Solver(graph)
# print(solver.validate_entity('/a', ast))
print(solver.model(ast))
