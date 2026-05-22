import os
import shlex
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass


ExternalCommand = str | Sequence[str]


@dataclass(frozen=True)
class ExternalAigerValidationResult:
    status: str
    command: tuple[str, ...] | None
    returncode: int | None
    stdout: str
    stderr: str
    message: str

    @property
    def passed(self) -> bool:
        return self.status == "passed"

    @property
    def failed(self) -> bool:
        return self.status == "failed"

    @property
    def skipped(self) -> bool:
        return self.status == "skipped"


def to_text(value: object) -> str:
    """Convert subprocess output-like values to text."""
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    if isinstance(value, bytearray):
        return bytes(value).decode("utf-8", errors="replace")

    if isinstance(value, memoryview):
        return value.tobytes().decode("utf-8", errors="replace")

    return str(value)


def environment_external_validator_command() -> str | None:
    """Return the optional external validator command from the environment.

    If set, the command is read from:

        STRING_TO_AIGER_EXTERNAL_AIGER_VALIDATOR

    The command may either contain `{path}` as a placeholder for the AIGER file
    or omit it. If omitted, the AIGER file path is appended automatically.
    """
    command = os.environ.get("STRING_TO_AIGER_EXTERNAL_AIGER_VALIDATOR")

    if command is None or command.strip() == "":
        return None

    return command


def build_external_command(
    command: ExternalCommand,
    aiger_path: str,
) -> tuple[str, ...]:
    """Build the concrete command used for external validation."""
    if isinstance(command, str):
        if "{path}" in command:
            return tuple(
                shlex.split(
                    command.replace("{path}", aiger_path)
                )
            )

        return tuple(shlex.split(command) + [aiger_path])

    parts = [
        part.replace("{path}", aiger_path)
        for part in command
    ]

    if not any("{path}" in part for part in command):
        parts.append(aiger_path)

    return tuple(parts)


def executable_exists(executable: str) -> bool:
    """Return True if the command executable appears to be available."""
    if os.path.isabs(executable):
        return os.path.exists(executable)

    if os.path.sep in executable:
        return os.path.exists(executable)

    return shutil.which(executable) is not None


def validate_aiger_with_external_tool(
    aiger_path: str,
    command: ExternalCommand | None = None,
    timeout_seconds: float = 10.0,
) -> ExternalAigerValidationResult:
    """Optionally validate an AIGER file with an external command.

    This function is intentionally optional. If no external command is provided,
    validation is skipped instead of failing. This keeps the project runnable
    without external dependencies.

    A command may be passed directly or configured through the environment
    variable STRING_TO_AIGER_EXTERNAL_AIGER_VALIDATOR.
    """
    if command is None:
        command = environment_external_validator_command()

    if command is None:
        return ExternalAigerValidationResult(
            status="skipped",
            command=None,
            returncode=None,
            stdout="",
            stderr="",
            message="No external AIGER validator command configured.",
        )

    if not os.path.exists(aiger_path):
        return ExternalAigerValidationResult(
            status="failed",
            command=None,
            returncode=None,
            stdout="",
            stderr="",
            message=f"AIGER file does not exist: {aiger_path}",
        )

    concrete_command = build_external_command(command, aiger_path)

    if not concrete_command:
        return ExternalAigerValidationResult(
            status="skipped",
            command=None,
            returncode=None,
            stdout="",
            stderr="",
            message="External AIGER validator command is empty.",
        )

    if not executable_exists(concrete_command[0]):
        return ExternalAigerValidationResult(
            status="skipped",
            command=concrete_command,
            returncode=None,
            stdout="",
            stderr="",
            message=f"External validator executable not found: {concrete_command[0]}",
        )

    try:
        completed = subprocess.run(
            concrete_command,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        return ExternalAigerValidationResult(
            status="failed",
            command=concrete_command,
            returncode=None,
            stdout=to_text(error.stdout),
            stderr=to_text(error.stderr),
            message="External AIGER validation timed out.",
        )

    if completed.returncode == 0:
        return ExternalAigerValidationResult(
            status="passed",
            command=concrete_command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            message="External AIGER validation passed.",
        )

    return ExternalAigerValidationResult(
        status="failed",
        command=concrete_command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        message="External AIGER validation failed.",
    )


def require_external_aiger_validation(
    aiger_path: str,
    command: ExternalCommand | None = None,
    timeout_seconds: float = 10.0,
) -> ExternalAigerValidationResult:
    """Run optional external validation and raise if it fails.

    Skipped validation is allowed because external tools are optional.
    """
    result = validate_aiger_with_external_tool(
        aiger_path=aiger_path,
        command=command,
        timeout_seconds=timeout_seconds,
    )

    if result.failed:
        raise ValueError(result.message)

    return result
