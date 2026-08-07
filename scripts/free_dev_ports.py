"""Free dev-server ports before starting the dashboard stack."""

from __future__ import annotations

import subprocess
import sys

PORTS = (5173, 8001, 8002)


def _pids_on_port_windows(port: int) -> set[int]:
    ps = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                f"(Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue "
                "| Select-Object -ExpandProperty OwningProcess -Unique) -join ' '"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    pids: set[int] = set()
    for token in ps.stdout.split():
        if token.isdigit():
            pids.add(int(token))
    return pids


def free_port_windows(port: int) -> None:
    for pid in _pids_on_port_windows(port):
        subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def main() -> int:
    if sys.platform == "win32":
        for port in PORTS:
            free_port_windows(port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
