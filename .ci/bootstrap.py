"""Validate deployment scaffolding and gate builds until complete source is supplied."""
import argparse
import json
from pathlib import Path


def code_present(root, required):
    present = [(root / name).is_file() for name in required]
    if not any(present):
        return False
    missing = [name for name, exists in zip(required, present) if not exists]
    if missing:
        raise ValueError("Application source is incomplete: " + ", ".join(missing))
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / ".ci/scaffold.json").read_text())
    for directory in ("deploy", ".ci"):
        for path in (root / directory).rglob("*.py"):
            compile(path.read_bytes(), str(path), "exec")
    ready = code_present(root, config["required_code"])
    if args.github_output:
        with args.github_output.open("a") as output:
            output.write("code_present=" + str(ready).lower() + "\n")
    print("Application source detected; full validation and deployment are enabled." if ready else "CI/CD scaffold is ready. Waiting for the first application-code push; no application is deployed.")


if __name__ == "__main__":
    main()
