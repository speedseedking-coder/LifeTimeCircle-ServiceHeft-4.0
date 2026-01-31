# tools/license_asset_audit.py
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:
    import tomllib  # py311+
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore

try:
    from importlib import metadata as importlib_metadata  # py>=3.8
except Exception:  # pragma: no cover
    import importlib_metadata  # type: ignore


SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    "storage",       # lokal (Uploads/Quarantine)
    "server/data",   # lokal (DB/Artefakte)
}

LICENSE_FILE_NAMES = {
    "LICENSE",
    "LICENSE.txt",
    "LICENSE.md",
    "COPYING",
    "COPYING.txt",
    "NOTICE",
    "NOTICE.txt",
    "THIRD_PARTY_NOTICES",
    "THIRD_PARTY_NOTICES.txt",
}

ASSET_EXT_GROUPS: Dict[str, str] = {
    # images
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".webp": "image",
    ".svg": "image",
    ".ico": "image",
    ".bmp": "image",

    # fonts
    ".ttf": "font",
    ".otf": "font",
    ".woff": "font",
    ".woff2": "font",
    ".eot": "font",

    # audio/video
    ".mp3": "audio",
    ".wav": "audio",
    ".ogg": "audio",
    ".m4a": "audio",
    ".mp4": "video",
    ".webm": "video",
    ".mov": "video",

    # web bundles
    ".js": "code-asset",
    ".mjs": "code-asset",
    ".cjs": "code-asset",
    ".css": "code-asset",
    ".map": "code-asset",

    # docs-like assets
    ".pdf": "doc-asset",
}

HEADER_SCAN_EXTS = {".js", ".mjs", ".cjs", ".css", ".ts", ".tsx", ".jsx"}
HEADER_SCAN_MAX_BYTES = 300_000  # nur kleine Files scannen (Headers)
HEADER_SCAN_MAX_LINES = 120

SPDX_RE = re.compile(r"SPDX-License-Identifier:\s*([A-Za-z0-9\.\-\+]+)")
LICENSE_WORD_RE = re.compile(r"\b(MIT|Apache|BSD|GPL|LGPL|AGPL|MPL|EPL|CDDL|Unlicense)\b", re.IGNORECASE)
COPYRIGHT_RE = re.compile(r"copyright", re.IGNORECASE)


@dataclass
class PythonDepLicenseRow:
    name: str
    version: str
    category: str
    license: str
    license_source: str
    home_page: str
    classifiers: List[str]
    notes: str


@dataclass
class AssetRow:
    path: str
    size_bytes: int
    sha256: str
    group: str
    license_hints: List[str]
    header_spdx: str
    header_keywords: List[str]
    header_has_copyright: bool
    notes: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_toml(path: Path) -> dict:
    if not tomllib:
        raise RuntimeError("tomllib nicht verfügbar. Bitte Python >= 3.11 nutzen (poetry env).")
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _norm_dist_name(name: str) -> str:
    # PEP503 normalization-ish: lower + replace runs of [-_.] with '-'
    n = name.strip().lower()
    return re.sub(r"[-_.]+", "-", n)


def _installed_metadata_map() -> Dict[str, object]:
    # map normalized dist-name -> metadata object
    out: Dict[str, object] = {}
    for dist in importlib_metadata.distributions():
        try:
            meta = dist.metadata
            dn = meta.get("Name") or dist.name
            if dn:
                out[_norm_dist_name(str(dn))] = meta
        except Exception:
            continue
    return out


def _extract_license_from_metadata(meta: object) -> Tuple[str, str, List[str]]:
    """
    Returns (license_str, source, classifiers)
    - license_str may be "UNKNOWN"
    - source indicates where it came from
    """
    license_val = ""
    classifiers: List[str] = []

    try:
        # email.message.Message-like
        license_val = str(getattr(meta, "get", lambda _k, _d=None: _d)("License", "") or "").strip()
        # Classifier can be multi-valued; metadata.get_all exists for some implementations
        get_all = getattr(meta, "get_all", None)
        if callable(get_all):
            classifiers = [str(x) for x in (get_all("Classifier") or [])]
        else:
            # fallback: attempt to split
            cls = getattr(meta, "get", lambda _k, _d=None: _d)("Classifier", None)
            if cls:
                classifiers = [str(cls)]
    except Exception:
        pass

    if license_val and license_val.upper() not in {"UNKNOWN", "NONE"}:
        return (license_val, "metadata:License", classifiers)

    # try to infer from classifiers
    lic_classes = [c for c in classifiers if c.lower().startswith("license ::")]
    if lic_classes:
        # prefer the most specific (usually last segment)
        # example: "License :: OSI Approved :: MIT License"
        best = lic_classes[0]
        # try to take last part
        parts = [p.strip() for p in best.split("::") if p.strip()]
        inferred = parts[-1] if parts else best
        return (inferred, "metadata:Classifier", classifiers)

    return ("UNKNOWN", "metadata:missing", classifiers)


def _extract_home_page(meta: object) -> str:
    for k in ("Home-page", "Project-URL", "Download-URL"):
        try:
            v = str(getattr(meta, "get", lambda _k, _d=None: _d)(k, "") or "").strip()
            if v:
                return v
        except Exception:
            continue
    return ""


def parse_poetry_lock(lock_path: Path) -> List[dict]:
    """
    Parses poetry.lock as TOML and returns list of package dicts:
      {name, version, category}
    """
    data = _read_toml(lock_path)
    pkgs = data.get("package", [])
    out: List[dict] = []
    if not isinstance(pkgs, list):
        return out
    for p in pkgs:
        if not isinstance(p, dict):
            continue
        name = str(p.get("name", "")).strip()
        version = str(p.get("version", "")).strip()
        category = str(p.get("category", "")).strip() or "main"
        if name and version:
            out.append({"name": name, "version": version, "category": category})
    # stable sort
    out.sort(key=lambda x: (_norm_dist_name(x["name"]), x["version"], x["category"]))
    return out


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def should_skip_dir(rel_dir: str) -> bool:
    rel_norm = rel_dir.replace("\\", "/").strip("/")
    if not rel_norm:
        return False
    parts = rel_norm.split("/")
    # exact matches
    if any(p in SKIP_DIR_NAMES for p in parts):
        return True
    # explicit composite paths (e.g. server/data)
    if rel_norm in SKIP_DIR_NAMES:
        return True
    # prefix checks
    for s in SKIP_DIR_NAMES:
        if "/" in s and rel_norm.startswith(s + "/"):
            return True
    return False


def find_license_hints(path: Path, repo_root: Path, max_depth_up: int = 6) -> List[str]:
    """
    Walk up from file's directory and collect nearby LICENSE/NOTICE files (paths relative to repo root).
    """
    hints: List[str] = []
    cur = path.parent
    depth = 0
    while True:
        depth += 1
        if depth > max_depth_up:
            break
        if repo_root in cur.parents or cur == repo_root:
            for fn in LICENSE_FILE_NAMES:
                cand = cur / fn
                if cand.exists() and cand.is_file():
                    hints.append(str(cand.relative_to(repo_root)).replace("\\", "/"))
        if cur == repo_root:
            break
        cur = cur.parent
    # unique keep order
    seen = set()
    uniq: List[str] = []
    for h in hints:
        if h not in seen:
            seen.add(h)
            uniq.append(h)
    return uniq


def scan_header_for_license_signals(path: Path) -> Tuple[str, List[str], bool]:
    """
    Returns (spdx_id, keywords, has_copyright)
    """
    spdx_id = ""
    keywords: List[str] = []
    has_cpr = False

    try:
        if path.stat().st_size > HEADER_SCAN_MAX_BYTES:
            return ("", [], False)
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()[:HEADER_SCAN_MAX_LINES]
        head = "\n".join(lines)

        m = SPDX_RE.search(head)
        if m:
            spdx_id = m.group(1).strip()

        kw = set()
        for m2 in LICENSE_WORD_RE.finditer(head):
            kw.add(m2.group(1).upper())
        keywords = sorted(kw)

        has_cpr = bool(COPYRIGHT_RE.search(head))
    except Exception:
        return ("", [], False)

    return (spdx_id, keywords, has_cpr)


def walk_repo_files(repo_root: Path) -> Iterable[Path]:
    for root, dirs, files in os.walk(repo_root):
        rel = os.path.relpath(root, repo_root)
        rel = "." if rel == os.curdir else rel
        if should_skip_dir(rel):
            dirs[:] = []
            continue

        # prune skipped dirs early
        pruned = []
        for d in list(dirs):
            drel = os.path.join(rel, d)
            if should_skip_dir(drel):
                pruned.append(d)
        for d in pruned:
            dirs.remove(d)

        for fn in files:
            p = Path(root) / fn
            yield p


def build_python_license_report(repo_root: Path) -> List[PythonDepLicenseRow]:
    lock_path = repo_root / "server" / "poetry.lock"
    if not lock_path.exists():
        return [
            PythonDepLicenseRow(
                name="__missing__",
                version="",
                category="",
                license="",
                license_source="",
                home_page="",
                classifiers=[],
                notes="server/poetry.lock nicht gefunden",
            )
        ]

    deps = parse_poetry_lock(lock_path)
    installed = _installed_metadata_map()

    rows: List[PythonDepLicenseRow] = []
    for d in deps:
        name = d["name"]
        version = d["version"]
        category = d["category"]

        meta = installed.get(_norm_dist_name(name))
        if meta is None:
            rows.append(
                PythonDepLicenseRow(
                    name=name,
                    version=version,
                    category=category,
                    license="UNKNOWN",
                    license_source="not-installed",
                    home_page="",
                    classifiers=[],
                    notes="Distribution im aktuellen Environment nicht gefunden (poetry install ausführen).",
                )
            )
            continue

        lic, src, classifiers = _extract_license_from_metadata(meta)
        home = _extract_home_page(meta)
        notes = ""
        if lic == "UNKNOWN":
            notes = "Lizenz fehlt in Metadaten; manuell prüfen (PyPI/GitHub/Projektseite)."
        rows.append(
            PythonDepLicenseRow(
                name=name,
                version=version,
                category=category,
                license=lic,
                license_source=src,
                home_page=home,
                classifiers=classifiers,
                notes=notes,
            )
        )

    return rows


def build_asset_inventory(repo_root: Path) -> List[AssetRow]:
    rows: List[AssetRow] = []
    for p in walk_repo_files(repo_root):
        rel = str(p.relative_to(repo_root)).replace("\\", "/")
        ext = p.suffix.lower()
        group = ASSET_EXT_GROUPS.get(ext, "")

        # treat only files that are "assets" OR likely embedded third-party bundles
        if not group:
            # still check big static-looking bundles by name patterns
            if ext in {".min.js", ".min.css"}:
                group = "code-asset"
            else:
                continue

        try:
            size = int(p.stat().st_size)
            digest = sha256_file(p)
        except Exception:
            continue

        hints = find_license_hints(p, repo_root)

        spdx_id = ""
        keywords: List[str] = []
        has_cpr = False
        if ext in HEADER_SCAN_EXTS:
            spdx_id, keywords, has_cpr = scan_header_for_license_signals(p)

        notes = ""
        if group in {"font", "code-asset"} and not hints and not spdx_id and not keywords and not has_cpr:
            notes = "Kein Lizenzhinweis gefunden; Quelle/Lizenz manuell nachziehen."
        elif group == "image" and not hints:
            notes = "Bild ohne nahe LICENSE/NOTICE; Quelle/Lizenz/Erstellung dokumentieren."

        rows.append(
            AssetRow(
                path=rel,
                size_bytes=size,
                sha256=digest,
                group=group,
                license_hints=hints,
                header_spdx=spdx_id,
                header_keywords=keywords,
                header_has_copyright=has_cpr,
                notes=notes,
            )
        )

    rows.sort(key=lambda r: (r.group, r.path))
    return rows


def md_escape(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ").strip()


def write_markdown_python(out_path: Path, rows: List[PythonDepLicenseRow]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    lines.append("# Third-Party Lizenzen – Python (poetry.lock)")
    lines.append("")
    lines.append(f"- Generiert: `{_utc_now_iso()}`")
    lines.append("- Quelle: `server/poetry.lock` + installierte Distribution-Metadaten (`importlib.metadata`).")
    lines.append("- Hinweis: `UNKNOWN`/`not-installed` muss manuell geklärt werden (kein Release ohne Klärung).")
    lines.append("")
    lines.append("| Paket | Version | Kategorie | Lizenz | Quelle | Home | Notes |")
    lines.append("|---|---:|---|---|---|---|---|")

    for r in rows:
        lines.append(
            f"| {md_escape(r.name)} | {md_escape(r.version)} | {md_escape(r.category)} | "
            f"{md_escape(r.license)} | {md_escape(r.license_source)} | {md_escape(r.home_page)} | {md_escape(r.notes)} |"
        )

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown_assets(out_path: Path, rows: List[AssetRow]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    lines.append("# Asset-Inventar (Lizenz-/Quellen-Check)")
    lines.append("")
    lines.append(f"- Generiert: `{_utc_now_iso()}`")
    lines.append("- Erfasst werden typische Assets (Bilder, Fonts, PDFs, JS/CSS-Bundles).")
    lines.append("- Ziel: Jede Datei braucht eine klare Quelle + Lizenz (oder “selbst erstellt”).")
    lines.append("")
    lines.append("| Typ | Pfad | Größe (Bytes) | SHA256 | Lizenz-Hinweise | SPDX | Keywords | Copyright? | Notes |")
    lines.append("|---|---|---:|---|---|---|---|---|---|")

    for r in rows:
        hints = ", ".join(r.license_hints) if r.license_hints else ""
        kws = ", ".join(r.header_keywords) if r.header_keywords else ""
        cpr = "yes" if r.header_has_copyright else ""
        lines.append(
            f"| {md_escape(r.group)} | {md_escape(r.path)} | {r.size_bytes} | {md_escape(r.sha256)} | "
            f"{md_escape(hints)} | {md_escape(r.header_spdx)} | {md_escape(kws)} | {cpr} | {md_escape(r.notes)} |"
        )

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(out_path: Path, py_rows: List[PythonDepLicenseRow], asset_rows: List[AssetRow]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    unknown_py = [r for r in py_rows if (r.license == "UNKNOWN" or r.license_source in {"not-installed", "metadata:missing"}) and r.name != "__missing__"]
    risky_assets = [a for a in asset_rows if a.notes]

    lines: List[str] = []
    lines.append("# Legal Summary (Lizenz/Assets)")
    lines.append("")
    lines.append(f"- Generiert: `{_utc_now_iso()}`")
    lines.append("")
    lines.append("## Stopper vor Verkauf")
    lines.append("")
    if not unknown_py and not risky_assets:
        lines.append("- Keine offenen Lizenz-/Asset-Hinweise gefunden (trotzdem finalen Review machen).")
    else:
        if unknown_py:
            lines.append("- Python: Pakete mit `UNKNOWN` / `not-installed` klären (Lizenzquelle nachziehen, ggf. ersetzen).")
        if risky_assets:
            lines.append("- Assets: Dateien ohne Lizenzhinweise/Quelle dokumentieren oder entfernen/ersetzen.")

    lines.append("")
    lines.append("## Nächste Schritte (konkret)")
    lines.append("")
    lines.append("1) Für jedes `UNKNOWN`-Paket: Projektseite/Repo prüfen, Lizenztext sichern, in `docs/legal/` dokumentieren.")
    lines.append("2) Für Fonts/Images/Bundles: Quelle + Lizenz + Nachweis (Screenshot/Link/Invoice) in eurem Legal-Ordner ablegen.")
    lines.append("3) Bei Copyleft (GPL/LGPL/AGPL): Lizenzpflichten prüfen (Linking/Distribution/SaaS); ggf. Alternative wählen.")
    lines.append("")
    lines.append("## Offene Posten – Python")
    lines.append("")
    if unknown_py:
        lines.append("| Paket | Version | Kategorie | LicenseSource | Notes |")
        lines.append("|---|---:|---|---|---|")
        for r in unknown_py:
            lines.append(
                f"| {md_escape(r.name)} | {md_escape(r.version)} | {md_escape(r.category)} | {md_escape(r.license_source)} | {md_escape(r.notes)} |"
            )
    else:
        lines.append("- Keine.")
    lines.append("")
    lines.append("## Offene Posten – Assets")
    lines.append("")
    if risky_assets:
        lines.append("| Typ | Pfad | Notes |")
        lines.append("|---|---|---|")
        for a in risky_assets:
            lines.append(f"| {md_escape(a.group)} | {md_escape(a.path)} | {md_escape(a.notes)} |")
    else:
        lines.append("- Keine.")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="License + Asset Audit (offline, repo-local)")
    ap.add_argument("--repo-root", default="", help="Projekt-Root. Default: Parent vom Script-Ordner.")
    ap.add_argument("--out-dir", default="docs/legal", help="Output-Ordner relativ zum Repo-Root.")
    ap.add_argument("--json", action="store_true", help="Zusätzlich JSON schreiben.")
    args = ap.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = Path(args.repo_root).resolve() if args.repo_root else script_dir.parent.resolve()
    out_dir = (repo_root / args.out_dir).resolve()

    py_rows = build_python_license_report(repo_root)
    asset_rows = build_asset_inventory(repo_root)

    py_md = out_dir / "THIRD_PARTY_PYTHON.md"
    assets_md = out_dir / "ASSET_INVENTORY.md"
    summary_md = out_dir / "LEGAL_SUMMARY.md"

    write_markdown_python(py_md, py_rows)
    write_markdown_assets(assets_md, asset_rows)
    write_summary(summary_md, py_rows, asset_rows)

    if args.json:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "third_party_python.json").write_text(
            json.dumps([asdict(r) for r in py_rows], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (out_dir / "asset_inventory.json").write_text(
            json.dumps([asdict(r) for r in asset_rows], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"[OK] Repo: {repo_root}")
    print(f"[OK] Reports: {out_dir}")
    print(f" - {py_md.relative_to(repo_root)}")
    print(f" - {assets_md.relative_to(repo_root)}")
    print(f" - {summary_md.relative_to(repo_root)}")
    if args.json:
        print(f" - {(out_dir / 'third_party_python.json').relative_to(repo_root)}")
        print(f" - {(out_dir / 'asset_inventory.json').relative_to(repo_root)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
