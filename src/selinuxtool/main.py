import argparse
import logging
import time
from pathlib import Path

from selinuxtool.android.graph import InfoFlowGraph
from selinuxtool.android.policy import Policy
from selinuxtool.ifdif.parser import Parser
from selinuxtool.ifdif.solver import Solver

parser = argparse.ArgumentParser(description='Evaluates SEAndroid policies.')
subparsers = parser.add_subparsers(help='set the execution mode', required=True)

# Vertical mode
parser_ver = subparsers.add_parser('vertical', help='compare policies of the same vendor/device')
parser_ver.add_argument(
    'vendor',
    type=str,
    help='a specific vendor if the -e option is used or the path of a collection of policies',
)
parser_ver.add_argument('device', nargs='?', help='a specific device')

# Policy mode
parser_pol = subparsers.add_parser('policy', help='compare the two provided policies')
parser_pol.add_argument('first', help='the first policy to compare')
parser_pol.add_argument('second', help='the second policy to compare')


# Generic setup
parser.add_argument('-v', '--verbose', action='store_true', help='prints debug info')
parser.add_argument(
    '-e', '--extracted', action='store_true', help='assume policies are from extracted folder'
)
parser.add_argument('-m', '--permmap', type=str, help='the path of the permission map to use')

# Save/Load functionality
save_load = parser.add_mutually_exclusive_group()
save_load.add_argument('-s', '--save', action='store_true', help='file contexts are saved to db')
save_load.add_argument(
    '-l',
    '--load',
    action='store_true',
    help='attempt to load file contexts from db; load from files and save otherwise',
)


SML_IND = ' ' * 2
MED_IND = SML_IND * 2
BIG_IND = SML_IND * 3


_logger = logging.getLogger('SELinuxTool')
_rlogger = logging.getLogger('SELinuxTool:r')
_flogger = logging.getLogger('SELinuxTool:f')
_blogger = logging.getLogger('SELinuxTool:b')
_extracted_path = Path('src/selinuxtool/android-extract/policies')
_permmapfile: Path | None = None


def main() -> None:
    args = parser.parse_args()

    for logger in [_logger, _rlogger, _flogger, _blogger]:
        logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    _permmapfile = Path(args.permmap) if args.permmap else None

    # Execute the subroutine
    args.func(args)


def vertical_mode(args: argparse.Namespace) -> None:
    _logger.info('Starting vertical comparison of the specified policies.')
    if not args.extracted:
        policy_root = Path(args.vendor)
    elif args.device:
        policy_root = _extracted_path / Path(args.vendor) / Path(args.device)
    else:
        policy_root = _extracted_path / Path(args.vendor)

    policy_paths: list[Path] = []
    for child in policy_root.iterdir():
        if not child.is_dir():
            continue
        policy_paths.append(child)
    policy_paths.sort()

    _logger.info(f'Found {len(policy_paths)} policies.')
    policies: list[Policy] = []
    for count, path in enumerate(policy_paths):
        # if count > 1:
        #     continue
        policy = Policy(path, _permmapfile)
        policy.load_policy(args.load, args.save, count)
        policies.append(policy)

    _logger.info('Ordering policies for vertical comparison:')
    policies.sort()
    for count, policy in enumerate(policies):
        _logger.info(f'  #{count + 1}: {policy.name} {policy.version}')

    _flogger.info(f'Vertical comparison of the following {len(policy_paths)} policies.')
    _logger.info('Stage 0 - stat differences:')
    _blogger.info(f'{BIG_IND}{Policy.STR_HEADERS}')
    for count, policy in enumerate(policies):
        _blogger.info(f'{SML_IND}#{count + 1}: {policy}')

    _blogger.info('Stage 1 - file context changes:')
    for i in range(len(policies) - 1):
        delta, dels, adds = policies[i].fc_diff(policies[i + 1])
        if delta:
            _blogger.info(f'{SML_IND}#{i + 1} --> #{i + 2} (-{dels}, +{adds})')
            for line in delta:
                _flogger.info(MED_IND + line)

    _blogger.info('Stage 2 - type changes:')
    for i in range(len(policies) - 1):
        nodes_self, nodes_other, edges_self, edges_other = policies[i].type_diff(policies[i + 1])
        if nodes_self or edges_self or nodes_other or edges_other:
            _blogger.info(
                f'{SML_IND}#{i + 1} --> #{i + 2}'
                f' Nodes (-{len(nodes_self)}, +{len(nodes_other)})'
                f' Edges (-{len(edges_self)}, +{len(edges_other)})'
            )
            if nodes_self or nodes_other:
                _flogger.info(f'{MED_IND}Node changes:')
                for node in nodes_self:
                    _flogger.info(f'{BIG_IND}- {node}')
                for node in nodes_other:
                    _flogger.info(f'{BIG_IND}+ {node}')
            if edges_self or edges_other:
                _flogger.info(f'{MED_IND}Edge changes:')
                for edge in edges_self:
                    _flogger.info(f'{BIG_IND}- {edge}')
                for edge in edges_other:
                    _flogger.info(f'{BIG_IND}+ {edge}')

    _blogger.info('Stage X - security changes:')
    for i in range(len(policies) - 1):
        diffs, nfa = policies[i].security_lvs_diff(policies[i + 1])
        if len(diffs) != 0:
            _blogger.info(f'{SML_IND}#{i + 1} --> #{i + 2} Diffs: {diffs}')
        if len(nfa.final_states) != 0:
            _blogger.info(f'{SML_IND}#{i + 1} --> #{i + 2} FC: {nfa}')

    _blogger.info('Stage Y - fc security changes:')
    for i in range(len(policies) - 1):
        graph = InfoFlowGraph(policies[i], policies[i + 1])
        graph.build_graph()
        nfa = graph.security_lvs_diff()
        if len(nfa.final_states) != 0:
            _blogger.info(f'{SML_IND}#{i + 1} --> #{i + 2} FC: {nfa}')
        del graph


def policy_mode(args: argparse.Namespace) -> None:
    _logger.info('Starting comparison of the specified policies.')

    policy_left = Policy(Path(args.first), _permmapfile)
    policy_right = Policy(Path(args.second), _permmapfile)
    policy_left.load_policy(args.load, args.save, 0)
    policy_right.load_policy(args.load, args.save, 1)

    graph = InfoFlowGraph(policy_left, policy_right)
    graph.build_graph()

    init_time = time.time()
    parser = Parser()
    solver = Solver(graph)
    queries = [
        'label_2 (CRITICAL) and not label_1 (CRITICAL)',
        'ito_2(label_2(CRITICAL) and not ito_1(label_2(CRITICAL)))',
        '(label_2(UNTRUSTED) and ito_2(label_2(CRITICAL))) and not (label_2(UNTRUSTED) and ito_1(label_2(CRITICAL)))',  # noqa: E501
        '(label_2(UNTRUSTED) and ito_2(label_2(CRITICAL))) and not (label_1(UNTRUSTED) and ito_1(label_1(CRITICAL)))',  # noqa: E501
        '(label_2(UNTRUSTED) and ito_2(label_2(CRITICAL)) and label_1(UNTRUSTED)) and not ito_1(label_1(CRITICAL))',  # noqa: E501
        '(label_2(CRITICAL) and ifrom_2(label_2(UNTRUSTED))) and not (label_2(CRITICAL) and ifrom_1(label_2(UNTRUSTED)))',  # noqa: E501
        '(ito_2(label_2(CRITICAL)) and label_1(UNTRUSTED)) and not label_2(TRUSTED)',
    ]
    for query in queries:
        ast = parser.solve(query)
        _logger.debug(solver.model(ast))
    query_time = time.time() - init_time
    _logger.info(f'Perfomed {len(queries)} queries in {query_time}.')


parser_ver.set_defaults(func=vertical_mode)
parser_pol.set_defaults(func=policy_mode)


if __name__ == '__main__':
    main()
