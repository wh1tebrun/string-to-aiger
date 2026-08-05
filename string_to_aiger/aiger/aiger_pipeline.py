import os

from string_to_aiger.aiger.aiger_validator import AigerHeader, validate_aiger


def write_text(path: str, text: str) -> None:
    output_dir = os.path.dirname(path)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def validate_and_write_aiger(path: str, aiger_text: str) -> AigerHeader:
    """Validate ASCII AIGER text and write it to disk."""
    header = validate_aiger(aiger_text)
    write_text(path, aiger_text)

    return header


def write_aiger_without_validation(path: str, aiger_text: str) -> None:
    """Write ASCII AIGER text to disk without validation."""
    write_text(path, aiger_text)
