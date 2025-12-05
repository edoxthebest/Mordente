import tempfile
from libmata import parser as mata_parser
import libmata.alphabets as mata_alph
import libmata.nfa.nfa as mata_nfa

_ascii = {chr(i): i for i in range(128)}
_alphabet = mata_alph.OnTheFlyAlphabet.from_symbol_map(_ascii)
_int_alph = mata_alph.IntAlphabet()

nfa = mata_parser.from_regex('/a')
print(nfa)
# print(mata_nfa.complement(nfa, _alphabet))
mata_str = nfa.to_mata_str()
print(mata_str)

tmp_file = tempfile.NamedTemporaryFile()

with open(tmp_file.name, 'w') as f:
    f.write(mata_str)

nfa_mata = mata_parser.from_mata(tmp_file.name, _int_alph)
print(nfa_mata)
print(nfa_mata.to_mata_str())


nfa_file = mata_parser.from_mata('selinuxtool/test.mata', _int_alph)
print(nfa_file.to_mata_str())

mata_str = """@NFA-explicit
%Alphabet-auto
%Initial q0
%Final q9
q0 47 q1
q1 97 q2
q2 100 q3
q3 98 q4
q4 95 q5
q5 107 q6
q6 101 q7
q7 121 q8
q8 115 q9
"""

tmp_file = tempfile.NamedTemporaryFile()

with open(tmp_file.name, 'w') as f:
    f.write(mata_str)

nfa_mata = mata_parser.from_mata(tmp_file.name, mata_alph.IntAlphabet())
print(nfa_mata)
print(nfa_mata.to_mata_str())
