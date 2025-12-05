# Adapted from BIGMAC
from __future__ import annotations

import json
import logging
import re
import tempfile
from pathlib import Path

from libmata import alphabets as mata_alph
from libmata import parser as mata_parser
from libmata.nfa import nfa as mata_nfa

_logger = logging.getLogger('SELinuxTool')
_rlogger = logging.getLogger('SELinuxTool:r')

_ascii = {chr(i): i for i in range(32, 127)}  # Except non-printable characters
_ascii_alphabet = mata_alph.OnTheFlyAlphabet.from_symbol_map(_ascii)


# File type (file object class)
# https://github.com/SELinuxProject/selinux-notebook/blob/main/src/seandroid.md#file_contexts
# -b - Block Device
# -c - Character Device
# -d - Directory
# -p - Named Pipe (FIFO)
# -l - Symbolic Link
# -s - Socket File
# -- - Ordinary file


class SELinuxContext:
    def __init__(self, user: str, role: str, type: str, mls_lv: str) -> None:
        self._user = user
        self._role = role
        self._type = type
        self._level = mls_lv

    def __str__(self) -> str:
        return f'{self._user}:{self._role}:{self._type}:{self._level}'

    @property
    def type(self) -> str:
        return self._type

    @staticmethod
    def from_string(ctx: str) -> SELinuxContext:
        components = ctx.split(':')

        if len(components) < 4:
            raise ValueError(f'Invalid SELinux label {ctx}')

        user = components[0]
        role = components[1]
        type = components[2]
        mls = ':'.join(components[3:])  # MLS is a special case and may also contain ':'

        return SELinuxContext(user, role, type, mls)


class FileContext:
    def __init__(
        self, regex: str | list, file_type: str, ctx: SELinuxContext, nfa: mata_nfa = None
    ) -> None:
        self._regex = [regex] if isinstance(regex, str) else regex
        self._ftype = file_type  # Future-proof
        self._ctx = ctx
        self._nfa = nfa

    @property
    def label(self) -> SELinuxContext:
        return self._ctx

    @property
    def regex(self) -> str:
        if self._nfa is not None:
            raise ValueError('Attempted access to regex after initial setup.')
        return self._regex[0]

    @property
    def nfa(self) -> mata_nfa:
        return self._nfa

    @nfa.setter
    def nfa(self, nfa: mata_nfa) -> None:
        self._nfa = nfa

    def add_regex(self, other: FileContext) -> None:
        if len(other._regex) != 1:
            raise ValueError
        self._regex.append(other._regex[0])

    # TODO: consider using json
    def to_db_string(self) -> str:
        ctx_string = f'{json.dumps(self._regex)}\t{self._ftype or ""}\t{self._ctx}'
        mata_string = self.nfa.to_mata_str()

        return f'--BEGIN--\n{ctx_string}\n{mata_string}--END--\n'

    @staticmethod
    def save(contexts: dict[str, FileContext], policy_path: str | Path) -> None:
        db_path = Path(policy_path) / 'db'
        db_path.mkdir(exist_ok=True)

        with open(db_path / 'file_contexts.db', 'w') as db:
            for _, ctx in contexts.items():
                db.write(ctx.to_db_string())

        _logger.info(f'Saved {len(contexts)} file contexts to db ({db_path}).')

    @staticmethod
    def load(policy_path: Path) -> dict[str, FileContext]:
        _rlogger.info('Loading file contexts from db.')
        contexts: dict[str, FileContext] = {}
        db_path = Path(policy_path) / 'db' / 'file_contexts.db'
        with open(db_path, 'r') as db:
            raw_db = db.read()
            ctx_expr = re.compile(
                r'^--BEGIN--\n([^\t]*)\t([^\s]*)\t([^\s]*)\n(.*?)\n--END--$',
                re.DOTALL | re.MULTILINE,
            )
            matches = ctx_expr.findall(raw_db)

            for progress, (regex, file_type, ctx, mata_str) in enumerate(matches):
                tmp_mata_file = tempfile.NamedTemporaryFile()
                with open(tmp_mata_file.name, 'w') as f:
                    f.write(mata_str)
                nfa = mata_parser.from_mata(tmp_mata_file.name, mata_alph.IntAlphabet())

                se_ctx = SELinuxContext.from_string(ctx)

                contexts[se_ctx.type] = FileContext(json.loads(regex), file_type, se_ctx, nfa)
                _rlogger.info(f'Loading file contexts from db {progress + 1} / {len(matches)}.')
        _logger.info(
            f'Loaded {len(contexts)} file contexts from db '
            f'({policy_path.name}/db/file_contexts.db).'
        )
        return contexts

    @staticmethod
    def from_files(ctx_paths: list[Path]) -> dict[str, FileContext]:
        contexts: list[FileContext] = []

        for ctx_path in ctx_paths:
            with open(ctx_path, 'r') as file:
                for line_no, line in enumerate(file):
                    # Ignore comments and blank lines
                    if re.match(r'^(\s*#)|(\s*$)', line):
                        continue

                    # Greedly replace all whitespace with a single space for splitting
                    line = re.sub(r'\s+', ' ', line)

                    # Split by spaces, while eliminating empty components
                    components = list(filter(lambda x: len(x) > 0, line.split(' ')))

                    match len(components):
                        case 3:
                            regex, ftype, ctx_str = components
                        case 2:
                            regex, ctx_str = components
                            ftype = ''
                        case _:
                            _logger.error(
                                f'Could not parse file context from {file} (line {line_no + 1}).'
                            )
                            continue

                    contexts.append(FileContext(regex, ftype, SELinuxContext.from_string(ctx_str)))

        # Contexts are processed from the last to the first
        contexts.reverse()

        # Construct NFA for each context regex
        old_nfa = mata_parser.from_regex('')
        for progress, ctx in enumerate(contexts):
            nfa = mata_parser.from_regex(ctx.regex)
            ctx.nfa = mata_nfa.intersection(nfa, mata_nfa.complement(old_nfa, _ascii_alphabet))
            old_nfa = mata_nfa.union(old_nfa, nfa)
            _rlogger.info(f'Reading file context {progress + 1} / {len(contexts)}.')
        _logger.info('')

        # Now with the NFA constructed we can aggregate them with no ordering issues
        contexts_dict: dict[str, FileContext] = {}
        repeated_ctx_count = 0
        for progress, ctx in enumerate(contexts):
            ctx_type = ctx.label.type
            if ctx_type not in contexts_dict:
                contexts_dict[ctx_type] = ctx
            else:
                repeated_ctx = contexts_dict[ctx_type]
                repeated_ctx.add_regex(ctx)
                repeated_ctx.nfa = mata_nfa.union(repeated_ctx.nfa, ctx.nfa)
                repeated_ctx_count += 1
            _rlogger.info(f'Aggregating file context {progress + 1} / {len(contexts)}')
        _logger.info(f'Read {len(contexts)} entries into {len(contexts_dict)} file contexts.')
        return contexts_dict
