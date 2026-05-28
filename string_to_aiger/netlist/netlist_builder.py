from string_to_aiger.logic.circuit import (
    BoolConst,
    InputVar,
    LengthIs,
    CharAtIs,
    And,
    Or,
    Expr,
)
from .netlist import Input, Const, AndGate, OrGate, Node


class NetlistBuilder:
    """Convert logical expressions into a gate-level netlist.

    LengthIs and CharAtIs are treated as primary input signals.

    This is intentional: the AIGER circuit does not store a concrete candidate
    string. Instead, it receives boolean facts such as "the candidate length is 4"
    or "the character at position 0 is a" as external input signals.
    The circuit then checks whether the required combination of these facts is
    sufficient to satisfy the compiled string constraint.
    """

    def __init__(self):
        self.nodes: dict[int, Node] = {}
        self.next_id = 1

        # Cache input nodes so repeated constraints such as len_is_4 or
        # x_0_is_a are represented by a single shared netlist input.
        self.input_cache: dict[str, int] = {}

    def new_node(self, node: Node) -> int:
        node_id = self.next_id
        self.nodes[node_id] = node
        self.next_id += 1
        return node_id

    def input_node(self, name: str) -> int:
        """Return the shared input node for a named boolean constraint."""
        if name in self.input_cache:
            return self.input_cache[name]

        node_id = self.new_node(Input(name))
        self.input_cache[name] = node_id
        return node_id

    def compile_expr(self, expr: Expr) -> int:
        if isinstance(expr, BoolConst):
            return self.new_node(Const(expr.value))

        if isinstance(expr, InputVar):
            return self.input_node(expr.name)

        if isinstance(expr, LengthIs):
            return self.input_node(f"len_is_{expr.value}")

        if isinstance(expr, CharAtIs):
            return self.input_node(f"x_{expr.index}_is_{expr.char}")

        if isinstance(expr, And):
            left_id = self.compile_expr(expr.left)
            right_id = self.compile_expr(expr.right)
            return self.new_node(AndGate(left_id, right_id))

        if isinstance(expr, Or):
            left_id = self.compile_expr(expr.left)
            right_id = self.compile_expr(expr.right)
            return self.new_node(OrGate(left_id, right_id))

        raise TypeError(f"Unknown expression type: {type(expr)}")
