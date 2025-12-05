# https://github.com/VeriFIT/mata
# pip install libmata  (require cmake installed)


from libmata import nfa, parser, alphabets

""" aut1 = parser.from_regex("/mnt/expand/[^/]+/app(/.*)?")
aut2 = parser.from_regex("/mnt/expand/[^/]+/local/tmp(/.*)?")

iaut = nfa.nfa.intersection(aut1, aut2) # nfa.nfa.determinize(nfa.nfa.intersection(aut1, aut2))

print(iaut.is_lang_empty()) """


def convert_and_union(res):
    """
    Given a list of regex, compute the corresponding automata and their union.
    """
    assert(len(res) > 0)
    head, tail = res[0], res[1:]
    aut_accumulator = parser.from_regex(head)

    for a in tail:
        aut = parser.from_regex(a)
        aut_accumulator = nfa.nfa.union(aut_accumulator, aut)

    return aut_accumulator

Ls = ['/mnt/expand/[^/]+/app(/.*)?', '/data/app(/.*)?']
Rs = [ ['/mnt/expand/[^/]+/local/tmp(/.*)?', '/data/local/tmp(/.*)?'], 
       ['/mnt/expand/[^/]+/app/vmdl[^/]+\\.tmp(/.*)?', '/data/app/vmdl[^/]+\\.tmp(/.*)?'],
       ['/data/misc/vold(/.*)?', '/mnt/expand/[^/]+/misc/vold(/.*)?', '/data/misc_ce/[0-9]+/vold(/.*)?', '/data/misc_de/[0-9]+/vold(/.*)?'],
       ['/mnt/expand/[^/]+/app/vmdl[^/]+\\.tmp/oat(/.*)?', '/data/app/vmdl[^/]+\\.tmp/oat(/.*)?', '/data/app/[^/]+/oat(/.*)?', '/mnt/expand/[^/]+/app/[^/]+/oat(/.*)?', '/data/dalvik-cache(/.*)?']
]


aut_ls = convert_and_union(Ls)

for r in Rs:
    print(f"Ls:{Ls}\nLr:{r}")
    aut_rs = convert_and_union(r)
    iaut = nfa.nfa.intersection(aut_ls, aut_rs)
    print(f"Intersection is empty? {iaut.is_lang_empty()}\n\n")




 
re = "/vendor/bin/hw/android\.hardware\.dumpstate@1\.0-service\.marlin"
print(parser.from_regex(re))