import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(ROOT_DIR, "outputs")

sys.path.append(ROOT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

from string_to_aiger.logic.circuit import And, InputVar  # noqa: E402
from string_to_aiger.sequential.sequential_circuit import SequentialCircuit  # noqa: E402
from string_to_aiger.sequential.sequential_aiger_writer import SequentialAigerWriter  # noqa: E402


def build_a_star_sequential_circuit() -> SequentialCircuit:
    """Manually construct a sequential circuit for a*.

    This demo is pedagogical: it shows the shape of a latch-based circuit by
    hand. In normal use, regex patterns are compiled automatically through the
    generic NFA-to-sequential pipeline, for example with:

        compile_regex_to_sequential("a*")
    """
    circuit = SequentialCircuit()

    circuit.add_input("is_a")
    circuit.add_input("end")

    alive = InputVar("alive")
    is_a = InputVar("is_a")
    end = InputVar("end")

    # alive means: all consumed symbols so far were 'a'.
    # Initially true, because the empty word is accepted by a*.
    next_alive = And(alive, is_a)

    circuit.add_latch("alive", next_alive, init=True)

    # Accept exactly when the input stream ends and the automaton is still alive.
    accept = And(end, alive)
    circuit.add_output("accept", accept)

    return circuit


def main():
    circuit = build_a_star_sequential_circuit()
    writer = SequentialAigerWriter(circuit)
    aiger_text = writer.write()

    output_path = os.path.join(OUTPUT_DIR, "sequential_astar.aag")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(aiger_text)

    print(aiger_text)
    print(f"\nWritten to {output_path}")


if __name__ == "__main__":
    main()
