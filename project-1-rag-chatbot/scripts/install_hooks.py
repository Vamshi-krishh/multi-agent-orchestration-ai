"""
Installs a post-merge git hook in every service under COMPONENTS_ROOT.
After installation, every `git pull` inside a service folder automatically
re-ingests that service into ChromaDB — no manual step needed.

Usage:
    python scripts/install_hooks.py          # install in all services
    python scripts/install_hooks.py kos      # install in specific service only
    python scripts/install_hooks.py --remove # remove hooks from all services
"""
import os
import sys
import stat

COMPONENTS_ROOT = r"C:\vamshi\COMPONENTS"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK_TEMPLATE = os.path.join(PROJECT_ROOT, "scripts", "post_merge_hook.sh")

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


def install_hook(service: str):
    hook_dir = os.path.join(COMPONENTS_ROOT, service, ".git", "hooks")
    hook_path = os.path.join(hook_dir, "post-merge")

    with open(HOOK_TEMPLATE, "r") as f:
        content = f.read()

    with open(hook_path, "w", newline="\n") as f:
        f.write(content)

    # Make executable
    current = os.stat(hook_path).st_mode
    os.chmod(hook_path, current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"[{service}] Hook installed at {hook_path}")


def remove_hook(service: str):
    hook_path = os.path.join(COMPONENTS_ROOT, service, ".git", "hooks", "post-merge")
    if os.path.exists(hook_path):
        os.remove(hook_path)
        print(f"[{service}] Hook removed")
    else:
        print(f"[{service}] No hook found — skipping")


def main():
    args = sys.argv[1:]
    remove = "--remove" in args
    only = [a for a in args if not a.startswith("--")]

    services = sorted([f for f in os.listdir(COMPONENTS_ROOT) if is_git_service(f)])
    if only:
        services = [s for s in services if s in only]

    if not services:
        print("No matching services found.")
        return

    action = "Removing hooks from" if remove else "Installing hooks in"
    print(f"{action} {len(services)} service(s)...\n")

    for service in services:
        try:
            remove_hook(service) if remove else install_hook(service)
        except Exception as e:
            print(f"[{service}] Error: {e}")

    print(f"\nDone. {'Run git pull inside any service to trigger auto re-ingestion.' if not remove else ''}")


if __name__ == "__main__":
    main()
