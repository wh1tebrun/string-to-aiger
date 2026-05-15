import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(ROOT_DIR, "outputs")

sys.path.append(ROOT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

from sequential_regex_compiler import compile_regex_to_sequential  # noqa: E402
from sequential_simulator import simulate  # noqa: E402
from sequential_aiger_writer import SequentialAigerWriter  # noqa: E402


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
    circuit = compile_regex_to_sequential(pattern)
    outputs = simulate(circuit, word_to_trace(word))
    return outputs[-1]["accept"]


def write_aiger(pattern: str, filename: str) -> None:
    circuit = compile_regex_to_sequential(pattern)
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


def main():
    run(
        "(a|b)*&a*",
        ["", "a", "aa", "aaa", "b", "ab", "ba"],
    )

    run(
        "(ab)*&(a|b)*",
        ["", "ab", "abab", "a", "b", "aba", "abb"],
    )

    run(
        "a*&b*",
        ["", "a", "aa", "b", "bb", "ab", "ba"],
    )

    write_aiger(
        "(a|b)*&a*",
        "sequential_intersection_output.aag",
    )


if __name__ == "__main__":
    main()
