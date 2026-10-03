"""Check Function declarations without the SDK's existing imported-module findings."""

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--follow-imports=silent",
            "tests/typing/functions_contract.py",
        ],
        cwd=root,
        env={**os.environ, "MYPYPATH": str(root / "src")},
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
