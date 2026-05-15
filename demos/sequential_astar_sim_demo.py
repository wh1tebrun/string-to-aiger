import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from sequential_astar_demo import build_a_star_sequential_circuit  # noqa: E402
from sequential_simulator import simulate  # noqa: E402


def word_to_trace(word: str) -> list[dict[str, bool]]:
    trace = []

    for ch in word:
        trace.append({
            "is_a": ch == "a",
            "end": False,
        })

    trace.append({
        "is_a": False,
        "end": True,
    })

    return trace


def accepts(word: str) -> bool:
    circuit = build_a_star_sequential_circuit()
    trace = word_to_trace(word)
    outputs = simulate(circuit, trace)

    return outputs[-1]["accept"]


words = ["", "a", "aa", "aaa", "b", "ab", "ba"]

for word in words:
    print(f"{word!r} -> {accepts(word)}")
