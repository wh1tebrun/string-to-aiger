from collections.abc import Mapping
from .netlist import Input, Const, AndGate, OrGate, Node


def pretty_netlist(nodes: Mapping[int, Node]) -> str:
    lines = []

    for node_id in sorted(nodes.keys()):
        node = nodes[node_id]

        if isinstance(node, Input):
            lines.append(f"{node_id}: INPUT {node.name}")
        elif isinstance(node, Const):
            lines.append(f"{node_id}: CONST {node.value}")
        elif isinstance(node, AndGate):
            lines.append(f"{node_id}: AND {node.left} {node.right}")
        elif isinstance(node, OrGate):
            lines.append(f"{node_id}: OR {node.left} {node.right}")
        else:
            lines.append(f"{node_id}: UNKNOWN")

    return "\n".join(lines)
