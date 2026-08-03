"""Capture runtime environment metadata for reproducibility."""

from __future__ import annotations

import platform
import sys
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version


def capture_environment() -> dict[str, str | list[str]]:
    """Return a JSON-serializable environment snapshot."""
    packages = []
    for package_name in ("msalgcm-optimize", "numpy", "pydantic", "typer"):
        try:
            packages.append(f"{package_name}=={version(package_name)}")
        except PackageNotFoundError:
            continue

    return {
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
        "machine": platform.machine(),
        "packages": packages,
    }
