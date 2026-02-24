#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LifeTimeCircle – ServiceHeft 4.0

BOM Gate: Fail if any UTF-8 BOM (EF BB BF) is present.

Default: tracked-only (git ls-files) -> stabil, CI-konform, keine False-Fails durch untracked lokale Dateien.
Optional: --all-files -> Vollscan per filesystem walk (skip dirs/prefixes).

Exit codes:
  0 -> OK: no BOM found
  1 -> FOUND: BOM present
  2 -> usage / unexpected error
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set

UTF8_BOM = b"\xEF\xBB\xBF"

DEFAULT_EXTS: Set[str] = {
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".py",
    ".ps1",
    ".ts",
    ".tsx",
    ".js",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".env",
}

# For --all-files only
SKIP_DIR_NAMES: Set[str] = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    ".vite",
    "artifacts",
}

SKIP_REL_PREFIXES: List[str] = [
    "server/data",
    "server/storage",
    "packages/web/node_modules",
    "packages/web/dist",
    "packages/web/.vite",
]


@dataclass(frozen=True)
class BomHit:
    path: str


def _posix_rel(root: Path, p: Path) -> str:
    root = root.resolve()
    p = p.resolve()
    return p.relative_to(root).as_posix()


def _git_ls_files(root: Path) -> Optional[List[str]]:
    try:
        r = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            capture_output=True,
            check=False,
        )
    except OSError:
        return None

    if r.returncode != 0:
        return None

    parts = r.stdout.split(b"\0")
    out: List[str] = []
    for b in parts:
        if not b:
            continue
        out.append(b.decode("utf-8", "surrogateescape"))
    out.sort()
    return out


def iter_tracked_files(root: Path, exts: Set[str]) -> Iterable[Path]:
    root = root.resolve()
    files = _git_ls_files(root)
    if files is None:
        raise RuntimeError("git ls-files failed (not a git repo or git not available).")

    for rel in files:
        p = (root / rel).resolve()
        if p.suffix.lower() not in exts:
            continue
        if not p.exists():
            raise FileNotFoundError(f"tracked file missing on disk: {rel}")
        yield p


def iter_all_files(root: Path, exts: Set[str]) -> Iterable[Path]:
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        dpath = Path(dirpath)

        # Deterministic order
        dirnames.sort()
        filenames.sort()

        rel_dir = _posix_rel(root, dpath)
        if rel_dir == ".":
            rel_dir = ""

        # prune by prefix
        for pref in SKIP_REL_PREFIXES:
            if rel_dir == pref or rel_dir.startswith(pref + "/"):
                dirnames[:] = []
                filenames[:] = []
                break

        # prune children
        pruned: List[str] = []
        for d in list(dirnames):
            if d in SKIP_DIR_NAMES:
                pruned.append(d)
                continue
            child = dpath / d
            rel_child = _posix_rel(root, child)
            for pref in SKIP_REL_PREFIXES:
                if rel_child == pref or rel_child.startswith(pref + "/"):
                    pruned.append(d)
                    break

        if pruned:
            pruned_set = set(pruned)
            dirnames[:] = [d for d in dirnames if d not in pruned_set]

        for fn in filenames:
            p = dpath / fn
            if p.suffix.lower() in exts:
                yield p.resolve()


def scan_bom(root: Path, exts: Set[str], all_files: bool) -> List[BomHit]:
    hits: List[BomHit] = []
    it = iter_all_files(root, exts) if all_files else iter_tracked_files(root, exts)

    for p in it:
        try:
            with open(p, "rb") as f:
                head = f.read(3)
            if head == UTF8_BOM:
                hits.append(BomHit(path=_posix_rel(root, p)))
        except OSError as e:
            raise OSError(f"cannot read: {p}: {e}") from e

    hits.sort(key=lambda h: h.path)
    return hits


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Fail if any UTF-8 BOM (EF BB BF) exists.")
    ap.add_argument("--root", default=".", help="Repo root to scan (default: .)")
    ap.add_argument(
        "--all-files",
        action="store_true",
        help="Scan all files via filesystem walk (default: tracked-only via git ls-files).",
    )
    ap.add_argument(
        "--ext",
        action="append",
        default=[],
        help="Additional extension to include (repeatable), e.g. --ext .csv",
    )
    ap.add_argument(
        "--only-ext",
        action="store_true",
        help="If set, scan ONLY the extensions provided via --ext (disables defaults).",
    )
    args = ap.parse_args(argv)

    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        print(f"ERROR: --root is not a directory: {root}", file=sys.stderr)
        return 2

    exts = set(e.lower() if e.startswith(".") else "." + e.lower() for e in args.ext)
    if args.only_ext:
        if not exts:
            print("ERROR: --only-ext requires at least one --ext", file=sys.stderr)
            return 2
    else:
        exts = set(DEFAULT_EXTS) | exts

    try:
        hits = scan_bom(root, exts, all_files=bool(args.all_files))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if hits:
        for h in hits:
            print(f"BOM: {h.path}")
        print(f"FOUND: {len(hits)} (UTF-8 BOM)")
        return 1

    print("OK: no UTF-8 BOM found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))