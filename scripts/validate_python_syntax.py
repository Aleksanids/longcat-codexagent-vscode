from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {"__pycache__", ".git"}


def iter_python_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        resolved = path if path.is_absolute() else ROOT / path
        if resolved.is_file() and resolved.suffix == ".py":
            files.append(resolved)
        elif resolved.is_dir():
            files.extend(
                item
                for item in resolved.rglob("*.py")
                if item.is_file() and not any(part in SKIP_PARTS for part in item.parts)
            )
    return sorted(set(files))


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Python syntax check without writing __pycache__.")
    parser.add_argument("paths", nargs="*", default=["scripts"], help="Files or directories to check.")
    args = parser.parse_args()
    files = iter_python_files([Path(item) for item in args.paths])
    errors: list[str] = []
    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
        except Exception as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
    if errors:
        print("PYTHON SYNTAX CHECK FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PYTHON SYNTAX CHECK OK")
    print(f"files={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
