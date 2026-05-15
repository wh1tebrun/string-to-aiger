import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from regex_parser import parse_regex  # noqa: E402
from regex_pretty import pretty_regex  # noqa: E402


examples = [
    "a",
    "ab",
    "a|b",
    "a*",
    "(ab)*",
    "(a|ba)*",
    "a*&b*",
    "(a|b)*&a*",
    "(a|ba)*&a*",
]

for example in examples:
    ast = parse_regex(example)
    print(example, "->", pretty_regex(ast))
