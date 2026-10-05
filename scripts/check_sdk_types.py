"""Require strict source types and positive/negative public Client consumer contracts.

Pass --wheel to check a built wheel in an isolated installation without source paths.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import venv
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "tests" / "typing"


def check_contracts(python: Path, directory: Path, *, installed: bool) -> int:
    env = os.environ.copy()
    env.pop("MYPYPATH", None)
    if installed:
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
    if not installed:
        env["MYPYPATH"] = str(ROOT / "src")
    common = [
        sys.executable,
        "-m",
        "mypy",
        "--config-file",
        str(ROOT / "pyproject.toml"),
        "--python-executable",
        str(python),
        "--show-error-codes",
        "--no-pretty",
    ]
    positive = [directory / "client_contract.py", directory / "functions_contract.py"]
    targets = [str(path) for path in positive]
    if not installed:
        targets.insert(0, str(ROOT / "src"))
    result = subprocess.run(
        [*common, *targets], cwd=directory, env=env, capture_output=True, text=True, check=False
    )
    print(result.stdout + result.stderr, end="", flush=True)
    if result.returncode:
        return result.returncode

    invalid = directory / "client_contract_invalid.py"
    expected = Counter()
    for line, source in enumerate(invalid.read_text().splitlines(), 1):
        if "# expect-error:" in source:
            codes = source.split("# expect-error:", 1)[1].split(",")
            expected.update((line, code.strip()) for code in codes)
    result = subprocess.run(
        [*common, str(invalid)],
        cwd=directory,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    actual = Counter()
    for match in re.finditer(r"^(.+?):(\d+): error: .*\[([^]]+)\]$", result.stdout, re.MULTILINE):
        path, line, code = match.groups()
        if (directory / path).resolve() != invalid.resolve():
            print(result.stdout + result.stderr, end="", flush=True)
            return 1
        actual[(int(line), code)] += 1
    if result.returncode != 1 or not expected or actual != expected:
        print(result.stdout + result.stderr, end="", flush=True)
        print(f"Expected diagnostics: {expected}; received: {actual}", flush=True)
        return 1
    print(
        f"Public Client negative contract: {sum(actual.values())} expected diagnostics", flush=True
    )
    return 0


def check_wheel(wheel: Path) -> int:
    wheel = wheel.resolve()
    with ZipFile(wheel) as archive:
        if "taruvi/py.typed" not in archive.namelist():
            print("Wheel is missing taruvi/py.typed", flush=True)
            return 1
    env = os.environ.copy()
    for key in ("MYPYPATH", "PYTHONPATH", "PYTHONHOME"):
        env.pop(key, None)
    with tempfile.TemporaryDirectory(prefix="taruvi-installed-types-") as temporary:
        directory = Path(temporary)
        environment = directory / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        install = subprocess.run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", str(wheel)],
            cwd=directory,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if install.returncode:
            print(install.stdout + install.stderr, end="", flush=True)
            return install.returncode
        # Confirm that the consumer imports the installed wheel, keeps the lazy
        # package import boundary, and sees the packaged marker at runtime.
        subprocess.run(
            [
                str(python),
                "-c",
                (
                    "import sys, taruvi; from pathlib import Path; "
                    "package = Path(taruvi.__file__).resolve(); "
                    "assert Path(sys.prefix).resolve() in package.parents, package; "
                    "assert package.with_name('py.typed').is_file(); "
                    "assert 'asyncio' not in sys.modules; "
                    "assert 'pydantic_settings' not in sys.modules; "
                    "print('Installed wheel marker and lazy import verified')"
                ),
            ],
            cwd=directory,
            env=env,
            check=True,
        )
        for path in CONTRACTS.glob("*.py"):
            shutil.copy2(path, directory / path.name)
        return check_contracts(python, directory, installed=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, help="Check an installed wheel instead of source")
    args = parser.parse_args()
    if args.wheel:
        return check_wheel(args.wheel)
    return check_contracts(Path(sys.executable), CONTRACTS, installed=False)


if __name__ == "__main__":
    raise SystemExit(main())
