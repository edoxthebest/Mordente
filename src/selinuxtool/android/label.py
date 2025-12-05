import logging
from enum import Flag, auto

_logger = logging.getLogger('SELinuxTool')


class EdgeType(Flag):
    NONE = 0
    READ = auto()
    WRITE = auto()
    UNKN = auto()
    ADDL = auto()
    BOTH = READ | WRITE

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}.{self.name}'

    # TRANSITION = 4
