#!/usr/bin/env node
"use strict";

/**
 * LifeTimeCircle – Service Heft 4.0
 * Deterministischer Encoding-/Mojibake-Scan (SoT)
 *
 * Output: JSONL (eine Zeile pro Treffer)
 * Record: { path, line, col, kind, match, snippet }
 *
 * Exit-Code:
 *   0 = keine Treffer
 *   1 = Treffer vorhanden
 *   2 = Tool-Error (z.B. Root invalid / Read error)
 *
 * WICHTIG:
 * - Das Tool enthält selbst Mojibake-Detektor-Literale (Ã/Â/â) in Regexen.
 *   Daher ist `tools/` standardmäßig excluded, um Self-Flagging zu vermeiden.
 */

const fs = require("fs");
const path = require("path");

// -------------------------
// Konfiguration (SoT)
// -------------------------

const ALLOWED_EXTS = new Set([".md", ".ts", ".tsx", ".js", ".py"]);

const REPLACEMENT_CHAR = "\uFFFD";
const REPLACEMENT_REGEX = /\uFFFD/g;

// Mojibake-Detektoren (typische UTF-8-as-Latin1/Win1252 Sequenzen)
const MOJIBAKE_DETECTORS = [
  // UTF-8 0xC3 xx -> "Ã" + Latin-1/Win1252 Char
  { kind: "mojibake_c3", regex: /Ã[\u00A0-\u00FF]/g },
  // UTF-8 0xC2 xx -> "Â" + Latin-1/Win1252 Char (häufig: NBSP)
  { kind: "mojibake_c2", regex: /Â[\u00A0-\u00FF]/g },
  // UTF-8 0xE2 0x80/0x84 ... -> typisches "â€…" / "â„…"
  { kind: "mojibake_e2_euro", regex: /â€[\s\S]/g },
  { kind: "mojibake_e2_tm", regex: /â„[\s\S]/g },
];

// Globale Excludes: diese Ordnernamen werden überall (auf jedem Level) ausgeschlossen
const EXCLUDE_DIR_NAMES_GLOBAL = new Set([
  ".git",
  "node_modules",
  "dist",
  "build",
  "coverage",
  ".pytest_cache",
  "artifacts",
  ".vite",
]);

// Prefix-Excludes (Pfad relativ zu --root, POSIX):
// Für projekt-spezifische Laufzeitdaten/Helpers/Outputs, die nicht Bestandteil des Scans sein sollen.
const EXCLUDE_PREFIXES = [
  "tools/", // Self-flagging vermeiden (Regex enthält Mojibake-Literale)
  "server/scripts/",
  "server/data/",
  "server/storage/",
  "data/", // lokale Rescue-Backups / Runtime
  "storage/",

  // web-spezifisch (redundant zu globalen dir-names, aber explizit erlaubt)
  "packages/web/node_modules/",
  "packages/web/dist/",
  "packages/web/.vite/",
];

function normalizePosixRel(posixRelPath) {
  // ensure POSIX slashes + remove leading "./"
  let p = posixRelPath.replace(/\\/g, "/");
  if (p.startsWith("./")) p = p.slice(2);
  return p;
}

function toPosixRelative(rootAbs, fileAbs) {
  const rel = path.relative(rootAbs, fileAbs);
  return rel.split(path.sep).join("/");
}

function isExcluded(posixRelPath) {
  const p = normalizePosixRel(posixRelPath);

  // 1) Prefix-Excludes (project-specific)
  if (EXCLUDE_PREFIXES.some((pref) => p === pref.slice(0, -1) || p.startsWith(pref))) return true;

  // 2) Global dir-name excludes (any level)
  const segs = p.split("/").filter(Boolean);
  for (const s of segs) {
    if (EXCLUDE_DIR_NAMES_GLOBAL.has(s)) return true;
  }

  return false;
}

function listFilesDeterministic(rootAbs) {
  /** @type {string[]} */
  const out = [];

  function walk(dirAbs) {
    const entries = fs.readdirSync(dirAbs, { withFileTypes: true });
    // deterministisch: lexikografisch sortieren
    entries.sort((a, b) => a.name.localeCompare(b.name, "en"));

    for (const ent of entries) {
      const abs = path.join(dirAbs, ent.name);
      const relPosix = toPosixRelative(rootAbs, abs);

      if (isExcluded(relPosix)) continue;

      if (ent.isDirectory()) {
        walk(abs);
        continue;
      }

      if (!ent.isFile()) continue;

      const ext = path.extname(ent.name).toLowerCase();
      if (!ALLOWED_EXTS.has(ext)) continue;

      out.push(abs);
    }
  }

  walk(rootAbs);

  // deterministisch: Pfade sortieren (über rel-posix, OS-unabhängig)
  out.sort((a, b) => {
    const ra = toPosixRelative(rootAbs, a);
    const rb = toPosixRelative(rootAbs, b);
    return ra.localeCompare(rb, "en");
  });

  return out;
}

function buildLineStarts(text) {
  const starts = [0];
  for (let i = 0; i < text.length; i++) {
    if (text.charCodeAt(i) === 10) starts.push(i + 1); // "\n"
  }
  return starts;
}

function findLineCol(lineStarts, index) {
  // Binary search: größte start <= index
  let lo = 0;
  let hi = lineStarts.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    const v = lineStarts[mid];
    if (v <= index) lo = mid + 1;
    else hi = mid - 1;
  }
  const lineIdx = Math.max(0, hi);
  const line = lineIdx + 1;
  const col = index - lineStarts[lineIdx] + 1;
  return { line, col };
}

function makeSnippet(text, index, length) {
  const before = 30;
  const after = 30;
  const start = Math.max(0, index - before);
  const end = Math.min(text.length, index + length + after);
  const raw = text.slice(start, end);
  return raw.replace(/\r/g, "").replace(/\n/g, "\\n");
}

function scanText(posixPath, text) {
  /** @type {{path:string,line:number,col:number,kind:string,match:string,snippet:string}[]} */
  const records = [];
  const lineStarts = buildLineStarts(text);

  // 1) Replacement Char (U+FFFD)
  REPLACEMENT_REGEX.lastIndex = 0;
  for (let m = REPLACEMENT_REGEX.exec(text); m !== null; m = REPLACEMENT_REGEX.exec(text)) {
    const idx = m.index;
    const lc = findLineCol(lineStarts, idx);
    records.push({
      path: posixPath,
      line: lc.line,
      col: lc.col,
      kind: "replacement_char",
      match: REPLACEMENT_CHAR,
      snippet: makeSnippet(text, idx, 1),
    });
  }

  // 2) Mojibake-Sequenzen
  for (const det of MOJIBAKE_DETECTORS) {
    det.regex.lastIndex = 0;
    for (let m = det.regex.exec(text); m !== null; m = det.regex.exec(text)) {
      const idx = m.index;
      const match = String(m[0] ?? "");
      const lc = findLineCol(lineStarts, idx);
      records.push({
        path: posixPath,
        line: lc.line,
        col: lc.col,
        kind: det.kind,
        match,
        snippet: makeSnippet(text, idx, match.length),
      });
    }
  }

  return records;
}

function sortRecordsDeterministic(records) {
  records.sort((a, b) => {
    const p = a.path.localeCompare(b.path, "en");
    if (p !== 0) return p;
    if (a.line !== b.line) return a.line - b.line;
    if (a.col !== b.col) return a.col - b.col;
    const k = a.kind.localeCompare(b.kind, "en");
    if (k !== 0) return k;
    return a.match.localeCompare(b.match, "en");
  });
}

function parseArgs(argv) {
  /** @type {{root:string}} */
  const opts = { root: "." };

  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];

    if (a === "--root") {
      const v = argv[i + 1];
      if (!v) throw new Error("Missing value for --root");
      opts.root = v;
      i++;
      continue;
    }

    if (a === "-h" || a === "--help") {
      printHelpAndExit(0);
    }

    throw new Error(`Unknown arg: ${a}`);
  }

  return opts;
}

function printHelpAndExit(code) {
  const msg = [
    "Usage:",
    "  node tools/mojibake_scan.js --root <path>",
    "",
    "Exit codes:",
    "  0 = no hits",
    "  1 = hits found",
    "  2 = tool error",
    "",
    "Output:",
    "  JSONL to stdout: {path,line,col,kind,match,snippet}",
  ].join("\n");
  process.stdout.write(msg + "\n");
  process.exit(code);
}

function main() {
  const opts = parseArgs(process.argv);

  const rootAbs = path.resolve(process.cwd(), opts.root);
  if (!fs.existsSync(rootAbs) || !fs.statSync(rootAbs).isDirectory()) {
    throw new Error(`--root is not a directory: ${rootAbs}`);
  }

  const files = listFilesDeterministic(rootAbs);

  /** @type {{path:string,line:number,col:number,kind:string,match:string,snippet:string}[]} */
  const all = [];

  for (const fileAbs of files) {
    const relPosix = toPosixRelative(rootAbs, fileAbs);

    let text;
    try {
      text = fs.readFileSync(fileAbs, "utf8");
    } catch {
      throw new Error(`Failed to read UTF-8: ${relPosix}`);
    }

    const recs = scanText(relPosix, text);
    for (const r of recs) all.push(r);
  }

  sortRecordsDeterministic(all);

  for (const r of all) {
    process.stdout.write(JSON.stringify(r) + "\n");
  }

  process.exitCode = all.length > 0 ? 1 : 0;
}

if (require.main === module) {
  try {
    main();
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    process.stderr.write(`ERROR: ${msg}\n`);
    process.exit(2);
  }
}