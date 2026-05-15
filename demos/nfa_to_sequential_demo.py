import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(ROOT_DIR, "outputs")

sys.path.append(ROOT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

from string_to_aiger.regex.regex_parser import parse_regex  # noqa: E402
from string_to_aiger.nfa.nfa_builder import build_nfa  # noqa: E402
from string_to_aiger.sequential.nfa_to_sequential import compile_nfa_to_sequential  # noqa: E402
from string_to_aiger.sequential.sequential_simulator import simulate  # noqa: E402
from string_to_aiger.sequential.sequential_aiger_writer import SequentialAigerWriter  # noqa: E402


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

    output_path = os.path.join(OUTPUT_DIR, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(aiger_text)

    print(f"Written to {output_path}")


def run(pattern: str, words: list[str]) -> None:
    print("Pattern:", pattern)

    for word in words:
        print(f"  {word!r} -> {accepts(pattern, word)}")

    print()


run("a*", ["", "a", "aa", "aaa", "b", "ab", "ba"])
run("(ab)*", ["", "ab", "abab", "a", "abb", "aba"])
run("(a|b)*", ["", "a", "b", "ab", "ba", "abba", "abc"])

write_aiger("a*", "sequential_generic_astar.aag")
