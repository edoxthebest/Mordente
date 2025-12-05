from selinuxtool.android.graph import InfoFlowGraph
from selinuxtool.android.policy import SecurityLvl
from selinuxtool.ifdif.ast import _POLICY, And, BDiamond, Diamond, Not, TruePolicy, UpArrow


class Solver:
    def __init__(self, info_flow_graph: InfoFlowGraph) -> None:
        self._graph = info_flow_graph

    def model(self, policy: _POLICY) -> set[tuple[str, str]]:
        match policy:
            case TruePolicy():
                return self._graph.labels

            case UpArrow():
                if policy.index not in {1, 2}:
                    raise IndexError(policy.index)

                match policy.label:
                    case SecurityLvl.UNTRUSTED:
                        if policy.index == 1:
                            labels = self._graph._left.untrusted_labels
                        elif policy.index == 2:
                            labels = self._graph._right.untrusted_labels

                    case SecurityLvl.TRUSTED:
                        if policy.index == 1:
                            labels = self._graph._left.trusted_labels
                        elif policy.index == 2:
                            labels = self._graph._right.trusted_labels

                    case SecurityLvl.CRITICAL:
                        if policy.index == 1:
                            labels = self._graph._left.critical_labels
                        elif policy.index == 2:
                            labels = self._graph._right.critical_labels

                    case _:
                        if not isinstance(policy.label, str):
                            raise TypeError('Cannot parse label.')
                        labels = [policy.label]

                return {t for t in self._graph.labels if t[policy.index - 1] in labels}

            case And():
                return self.model(policy.left) & self.model(policy.right)

            case Not():
                return self._graph.labels - self.model(policy.inner)

            case Diamond():
                candidates = self.model(policy.policy)
                if not candidates:
                    return set()

                if policy.index == 1:
                    direction = 'left'
                elif policy.index == 2:
                    direction = 'right'
                else:
                    raise IndexError(policy.index)

                return self._graph.eventually_reach(candidates, direction)

            case BDiamond():
                candidates = self.model(policy.policy)
                if not candidates:
                    return set()

                if policy.index == 1:
                    direction = 'left'
                elif policy.index == 2:
                    direction = 'right'
                else:
                    raise IndexError(policy.index)

                return self._graph.eventually_reached_by(candidates, direction)

            case _:
                raise TypeError('Unrecognised logical component.')
