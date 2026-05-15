import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from circuit import And, InputVar  # noqa: E402
from sequential_circuit import SequentialCircuit  # noqa: E402
from sequential_aiger_writer import SequentialAigerWriter  # noqa: E402


def build_a_star_sequential_circuit() -> SequentialCircuit:
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

    with open("sequential_astar.aag", "w", encoding="utf-8") as f:
        f.write(aiger_text)

    print(aiger_text)
    print("\nWritten to sequential_astar.aag")


if __name__ == "__main__":
    main()
