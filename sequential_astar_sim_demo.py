from sequential_astar_demo import build_a_star_sequential_circuit
from sequential_simulator import simulate


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