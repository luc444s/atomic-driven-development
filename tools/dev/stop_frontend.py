from __future__ import annotations

import os
import signal
import subprocess


def main() -> None:
    current_pid = os.getpid()
    result = subprocess.run(
        ["pgrep", "-af", "vite|pnpm.*@systutor/web dev|npm run frontend"],
        capture_output=True,
        text=True,
        check=False,
    )

    stopped = False
    for line in result.stdout.splitlines():
        parts = line.strip().split(maxsplit=1)
        if not parts:
            continue

        try:
            pid = int(parts[0])
        except ValueError:
            continue

        command = parts[1] if len(parts) > 1 else ""
        if pid == current_pid or "frontend:stop" in command:
            continue
        if (
            "@systutor/web dev" not in command
            and "vite/bin/vite.js" not in command
            and command != "npm run frontend"
        ):
            continue

        os.kill(pid, signal.SIGTERM)
        print(f"Frontend detenido (pid={pid})")
        stopped = True

    if not stopped:
        print("No hay frontend corriendo")


if __name__ == "__main__":
    main()
