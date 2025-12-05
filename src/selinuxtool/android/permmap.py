import logging
from dataclasses import dataclass
from pathlib import Path

from setools.exception import UnmappedClass, UnmappedPermission
from setools.permmap import Mapping, PermissionMap
from setools.policyrep import AVRule

_logger = logging.getLogger('SELinuxTool')


@dataclass
class RuleInfoFlow:
    read: int
    write: int
    read_perms: list[str]
    write_perms: list[str]
    unknown_perms: list[str]

    @property
    def perms(self) -> list[str]:
        return self.read_perms + self.write_perms + self.unknown_perms


class AndroidPermissionMap(PermissionMap):
    def __init__(self, permmapfile: str | Path | None = None) -> None:
        super().__init__(permmapfile)

    def rule_infoflow(self, rule: AVRule) -> RuleInfoFlow:
        rule_class = str(rule.tclass)
        max_read_weight = 0
        max_write_weight = 0
        read_perms = []
        write_perms = []
        unknown_perms = []

        # if rule.ruletype != TERuletype.allow:
        #     raise exception.RuleTypeError("{0} rules cannot be used for calculating a weight".
        #                                   format(rule.ruletype))

        # Iterate over the permissions and determine the direction and weight for each
        for perm in rule.perms:
            try:
                mapping = Mapping(self._permmap, rule_class, perm)
            except UnmappedClass:
                unknown_perms.append(perm)
                # _logger.warning('Unmapped permission class: ' + rule_class)
                continue
            except UnmappedPermission:
                unknown_perms.append(perm)
                # _logger.warning('Unmapped permission: ' + rule_class + ':' + perm)
                continue

            if not mapping.enabled:
                continue

            if mapping.direction == 'r':
                read_perms.append(perm)
                max_read_weight = max(max_read_weight, mapping.weight)
            elif mapping.direction == 'w':
                write_perms.append(perm)
                max_write_weight = max(max_write_weight, mapping.weight)
            elif mapping.direction == 'b':
                read_perms.append(perm)
                max_read_weight = max(max_read_weight, mapping.weight)
                write_perms.append(perm)
                max_write_weight = max(max_write_weight, mapping.weight)

        return RuleInfoFlow(
            max_read_weight, max_write_weight, read_perms, write_perms, unknown_perms
        )
