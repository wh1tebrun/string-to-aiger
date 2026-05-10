from regex_parser import parse_regex
from nfa_builder import build_nfa
from nfa_to_sequential import compile_nfa_to_sequential
from sequential_simulator import simulate
from sequential_aiger_writer import SequentialAigerWriter


def word_to_trace(word: str) -> list[dict[str, bool]]:
    trace = []

    for ch in word:
        trace.append({
            f"is_{ch}": True,
            "end": False,
        })

    trace.append({
        "end": True,
    })

    return trace


def accepts(pattern: str, word: str) -> bool:
    ast = parse_regex(pattern)
    nfa = build_nfa(ast)
    circuit = compile_nfa_to_sequential(nfa)

    outputs = simulate(circuit, word_to_trace(word))
    return outputs[-1]["accept"]


def write_aiger(pattern: str, filename: str) -> None:
    ast = parse_regex(pattern)
    nfa = build_nfa(ast)
    circuit = compile_nfa_to_sequential(nfa)

    writer = SequentialAigerWriter(circuit)
    aiger_text = writer.write()

    with open(filename, "w", encoding="utf-8") as f:
        f.write(aiger_text)


def run(pattern: str, words: list[str]) -> None:
    print("Pattern:", pattern)

    for word in words:
        print(f"  {word!r} -> {accepts(pattern, word)}")

    print()


run("a*", ["", "a", "aa", "aaa", "b", "ab", "ba"])
run("(ab)*", ["", "ab", "abab", "a", "abb", "aba"])
run("(a|b)*", ["", "a", "b", "ab", "ba", "abba", "abc"])

write_aiger("a*", "sequential_generic_astar.aag")
print("Written to sequential_generic_astar.aag")