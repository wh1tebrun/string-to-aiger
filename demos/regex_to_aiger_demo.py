import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(ROOT_DIR, "outputs")

sys.path.append(ROOT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

from regex_to_aiger import compile_regex_to_aiger  # noqa: E402


def main():
    pattern = "a*"
    bound = 3

    aiger_text = compile_regex_to_aiger(pattern, bound)

    output_path = os.path.join(OUTPUT_DIR, "regex_output.aag")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(aiger_text)

    print("Pattern:", pattern)
    print("Bound:", bound)
    print(f"Written to {output_path}")


if __name__ == "__main__":
    main()
