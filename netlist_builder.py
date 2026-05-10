from circuit import BoolConst, InputVar, LengthIs, CharAtIs, And, Or, Expr
from netlist import Input, Const, AndGate, OrGate, Node


class NetlistBuilder:
    """Convert logical expressions into a gate-level netlist."""
    def __init__(self):
        self.nodes: dict[int, Node] = {}
        self.next_id = 1
        self.input_cache: dict[str, int] = {}

    def new_node(self, node: Node) -> int:
        node_id = self.next_id
        self.nodes[node_id] = node
        self.next_id += 1
        return node_id

    def compile_expr(self, expr: Expr) -> int:
        if isinstance(expr, BoolConst):
            return self.new_node(Const(expr.value))
        
        if isinstance(expr, InputVar):
            name = expr.name
            if name in self.input_cache:
                return self.input_cache[name]
            
            node_id = self.new_node(Input(name))
            self.input_cache[name] = node_id
            return node_id

        if isinstance(expr, LengthIs):
            name = f"len_is_{expr.value}"
            if name in self.input_cache:
                return self.input_cache[name]
            node_id = self.new_node(Input(name))
            self.input_cache[name] = node_id
            return node_id

        if isinstance(expr, CharAtIs):
            name = f"x_{expr.index}_is_{expr.char}"
            if name in self.input_cache:
                return self.input_cache[name]
            node_id = self.new_node(Input(name))
            self.input_cache[name] = node_id
            return node_id

        if isinstance(expr, And):
            left_id = self.compile_expr(expr.left)
            right_id = self.compile_expr(expr.right)
            return self.new_node(AndGate(left_id, right_id))

        if isinstance(expr, Or):
            left_id = self.compile_expr(expr.left)
            right_id = self.compile_expr(expr.right)
            return self.new_node(OrGate(left_id, right_id))

        raise TypeError(f"Unknown expression type: {type(expr)}")
