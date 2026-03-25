"""Reproducibility helpers shared across EpiClaw skills."""

from __future__ import annotations

from pathlib import Path

from checksums import sha256_file


def write_commands_script(path: str | Path, commands: list[str]) -> Path:
    """Write a simple shell script containing the executed or recommended commands."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["#!/usr/bin/env bash", "set -euo pipefail", ""] + commands
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        path.chmod(0o755)
    except OSError:
        pass
    return path


def write_checksums_manifest(base_dir: str | Path, files: list[str | Path], output_name: str = "checksums.sha256") -> Path:
    """Write a sha256 manifest for the provided files relative to base_dir."""
    base_dir = Path(base_dir)
    manifest_path = base_dir / output_name
    lines: list[str] = []
    for file_path in files:
        file_path = Path(file_path)
        if file_path.exists() and file_path.is_file():
            try:
                relative = file_path.relative_to(base_dir.parent)
            except ValueError:
                relative = file_path.name
            lines.append(f"{sha256_file(file_path)}  {relative}")
    manifest_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return manifest_path
