from string_to_aiger.netlist.netlist_builder import NetlistBuilder
from .aiger_writer import AigerWriter


def compile_expr_to_aiger(expr):
    """Compile a logical expression into ASCII AIGER."""
    builder = NetlistBuilder()
    output_id = builder.compile_expr(expr)
    writer = AigerWriter(builder.nodes, output_id)
    return writer.write()
