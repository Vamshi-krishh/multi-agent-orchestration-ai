"""
Pull latest code for all (or specific) services in COMPONENTS,
then re-ingest only the services that actually changed.

Usage:
    python scripts/pull_and_reingest.py              # pull + reingest all changed services
    python scripts/pull_and_reingest.py kos icps     # pull + reingest specific services only
"""
import os
import sys
import subprocess

COMPONENTS_ROOT = r"C:\vamshi\COMPONENTS"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = os.path.join(PROJECT_ROOT, "venv", "Scripts", "python.exe")
INGEST_SCRIPT = os.path.join(PROJECT_ROOT, "ingest_all.py")

SKIP_FOLDERS = {
    ".github", ".metadata", ".pytest_cache", ".vscode",
    "knowledge-base", "mcp-server", "isep-ui"
}


def is_git_service(folder: str) -> bool:
    path = os.path.join(COMPONENTS_ROOT, folder)
    return (
        os.path.isdir(path)
        and folder not in SKIP_FOLDERS
        and os.path.isdir(os.path.join(path, ".git"))
    )


def git_pull(service_path: str) -> str:
    result = subprocess.run(
        ["git", "pull"],
        cwd=service_path,
        capture_output=True,
        text=True
    )
    return (result.stdout + result.stderr).strip()


def had_changes(pull_output: str) -> bool:
    already_up_to_date = (
        "already up to date" in pull_output.lower()
        or pull_output == ""
    )
    return not already_up_to_date


def main(only: list[str] = None):
    all_services = sorted([
        f for f in os.listdir(COMPONENTS_ROOT)
        if is_git_service(f)
    ])

    services = [s for s in all_services if s in only] if only else all_services

    if not services:
        print("No matching services found.")
        return

    print(f"Pulling {len(services)} service(s)...\n")

    changed = []
    for service in services:
        service_path = os.path.join(COMPONENTS_ROOT, service)
        output = git_pull(service_path)
        if had_changes(output):
            print(f"[{service}] Updated — will re-ingest")
            print(f"  {output[:120]}")
            changed.append(service)
        else:
            print(f"[{service}] Already up to date")

    print()

    if not changed:
        print("Nothing changed. ChromaDB is already up to date.")
        return

    print(f"Re-ingesting {len(changed)} service(s): {changed}\n")
    subprocess.run([PYTHON, INGEST_SCRIPT] + changed)
    print("\nDone. ChromaDB is up to date.")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(only=args if args else None)
