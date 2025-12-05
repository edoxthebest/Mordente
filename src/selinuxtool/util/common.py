from libmata.nfa import strings as mata_str
from libmata.nfa.nfa import Nfa as Nfa


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def nfa_to_word(nfa: Nfa) -> str:
    words = []
    shortest_words = mata_str.get_shortest_words(nfa)
    for word in shortest_words:
        chars = [chr(c) for c in word]
        words.append(''.join(chars))
    return words
