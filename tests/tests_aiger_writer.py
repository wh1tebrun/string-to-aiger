"""Focused combinational writer regressions; no external tools required."""
from collections.abc import Callable
from itertools import product

from string_to_aiger.aiger.aiger import compile_expr_to_aiger
from string_to_aiger.aiger.aiger_writer import AigerWriter
from string_to_aiger.logic.circuit import And, InputVar, Or
from string_to_aiger.netlist.netlist import AndGate, Const, Input, OrGate


def evaluate_aag(text: str, inputs: dict[str, bool]) -> bool:
    """Interpret only the single-output combinational AAG subset tested here."""
    lines = text.splitlines()
    kind, maximum, num_inputs, num_latches, num_outputs, num_ands = lines[0].split()
    maximum, num_inputs, num_latches, num_outputs, num_ands = map(
        int, (maximum, num_inputs, num_latches, num_outputs, num_ands)
    )
    assert kind == "aag" and num_latches == 0 and num_outputs == 1
    symbols = lines[2 + num_inputs + num_ands:]
    names = {}
    for line in symbols:
        if line == "c":
            break
        index, name = line.split(maxsplit=1)
        if index.startswith("i"):
            names[int(index[1:])] = name
    assert set(names) == set(range(num_inputs))
    assert set(inputs) == set(names.values())
    values = {0: False}
    for index, line in enumerate(lines[1:1 + num_inputs]):
        literal = int(line)
        assert literal > 1 and literal % 2 == 0 and literal // 2 not in values
        values[literal // 2] = inputs[names[index]]

    def value(literal: int) -> bool:
        assert 0 <= literal <= 2 * maximum + 1
        return values[literal // 2] != bool(literal & 1)

    output = int(lines[1 + num_inputs])
    for line in lines[2 + num_inputs:2 + num_inputs + num_ands]:
        lhs, left, right = map(int, line.split())
        assert lhs > 1 and lhs % 2 == 0 and lhs // 2 not in values
        values[lhs // 2] = value(left) and value(right)
    return value(output)


def assert_truth_table(
    text: str, names: list[str], oracle: Callable[[dict[str, bool]], bool]
) -> None:
    for bits in product((False, True), repeat=len(names)):
        inputs = dict(zip(names, bits))
        expected = oracle(inputs)
        actual = evaluate_aag(text, inputs)
        assert actual == expected, (
            f"truth-table mismatch: {inputs}, expected {expected}, actual {actual}"
        )


def test_shared_or_under_and() -> None:
    nodes = {
        1: Input("x"), 2: Input("y"),
        3: OrGate(1, 2), 4: AndGate(3, 3),
    }
    writer = AigerWriter(nodes, 4)
    text = writer.write()
    assert_truth_table(text, ["x", "y"], lambda v: v["x"] or v["y"])
    assert writer.ands == [(6, 3, 5), (8, 7, 7)]


def test_repeated_or_returns_semantic_literal_without_new_gates() -> None:
    writer = AigerWriter({1: Input("x"), 2: Input("y"), 3: OrGate(1, 2)}, 3)
    first = writer.compile_node(3)
    rows = list(writer.ands)
    assert first == 7 and first % 2 == 1
    for _ in range(3):
        assert writer.compile_node(3) == first
        assert writer.and_literals[3] == first
        assert writer.ands == rows == [(6, 3, 5)]
        assert writer.next_var == 4


def test_shared_or_through_different_and_or_parents() -> None:
    nodes = {
        1: Input("x"), 2: Input("y"), 3: Input("z"),
        4: OrGate(1, 2), 5: AndGate(4, 3),
        6: OrGate(4, 3), 7: OrGate(5, 6),
    }
    writer = AigerWriter(nodes, 7)
    text = writer.write()
    assert_truth_table(
        text, ["x", "y", "z"],
        lambda v: ((v["x"] or v["y"]) and v["z"])
        or ((v["x"] or v["y"]) or v["z"]),
    )
    assert len(writer.ands) == 4
    rows = list(writer.ands)
    for node_id in (4, 5, 6, 7):
        assert writer.compile_node(node_id) == writer.and_literals[node_id]
    assert writer.ands == rows


def test_shared_and_keeps_positive_cached_literal() -> None:
    writer = AigerWriter(
        {1: Input("x"), 2: Input("y"), 3: AndGate(1, 2), 4: OrGate(3, 3)}, 4
    )
    text = writer.write()
    assert_truth_table(text, ["x", "y"], lambda v: v["x"] and v["y"])
    assert writer.compile_node(3) == writer.and_literals[3] == 6
    assert writer.ands == [(6, 2, 4), (8, 7, 7)]


def test_constants_and_direct_or_output() -> None:
    for constant in (False, True):
        writer = AigerWriter({1: Const(constant)}, 1)
        assert_truth_table(writer.write(), [], lambda _v: constant)
        assert writer.compile_node(1) == int(constant)
        assert writer.ands == []

        writer = AigerWriter({1: Const(constant), 2: Input("x"), 3: OrGate(1, 2)}, 3)
        text = writer.write()
        assert_truth_table(text, ["x"], lambda v: constant or v["x"])
        output = int(text.splitlines()[2])
        assert output % 2 == 1
        assert writer.compile_node(3) == output
        assert len(writer.ands) == 1 and writer.ands[0][0] % 2 == 0


def test_normal_expr_builder_control() -> None:
    shared_expr = Or(InputVar("x"), InputVar("y"))
    text = compile_expr_to_aiger(And(shared_expr, shared_expr))
    assert_truth_table(text, ["x", "y"], lambda v: v["x"] or v["y"])
    # The ordinary builder shares named inputs, but duplicates the OR gates.
    assert text.splitlines()[0] == "aag 5 2 0 1 3"


def run_tests() -> None:
    test_shared_or_under_and()
    test_repeated_or_returns_semantic_literal_without_new_gates()
    test_shared_or_through_different_and_or_parents()
    test_shared_and_keeps_positive_cached_literal()
    test_constants_and_direct_or_output()
    test_normal_expr_builder_control()
    print("All AIGER writer cache-polarity tests passed.")


if __name__ == "__main__":
    run_tests()
