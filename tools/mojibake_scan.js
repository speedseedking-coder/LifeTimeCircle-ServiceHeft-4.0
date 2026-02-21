#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { TextDecoder } = require("util");

/**
 * Deterministischer Mojibake/Replacement-Char Scanner (JSONL)
 * Records: { path, line, col, kind, match, snippet }
 *
 * Exit code:
 *  - 0: keine Treffer
 *  - 1: Treffer vorhanden
 *  - 2: CLI/Runtime error
 */

const DEFAULT_ALLOW_EXT = [".md", ".ts", ".tsx", ".js", ".py"];
const DEFAULT_EXCLUDE_SEGMENTS = [
  ".git",
  "node_modules",
  "dist",
  "server/scripts",
  // "tools", // bewusst NICHT default-excluded (Scanner soll Tools selbst prüfen können)
  "server/data",
  "server/storage",
  "packages/web/dist",
  "packages/web/node_modules",
  "packages/web/.vite",
].map((s) => s.toLowerCase());

const decoder = new TextDecoder("utf-8", { fatal: false });

function toPosix(p) {
  return p.split(path.sep).join("/");
}

function relPosix(rootAbs, abs) {
  return toPosix(path.relative(rootAbs, abs)).replace(/^(\.\/)+/, "");
}

function parseExtList(s) {
  return s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean)
    .map((x) => (x.startsWith(".") ? x.toLowerCase() : "." + x.toLowerCase()));
}

function parseArgs(argv) {
  const args = {
    root: process.cwd(),
    allowExt: new Set(DEFAULT_ALLOW_EXT),
    excludeSegments: new Set(DEFAULT_EXCLUDE_SEGMENTS),
    maxBytes: 2 * 1024 * 1024, // 2MB default safety
    help: false,
  };

  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];

    if (a === "-h" || a === "--help") {
      args.help = true;
      continue;
    }

    if (a === "--root") {
      const v = argv[++i];
      if (!v) throw new Error("Missing value for --root");
      args.root = path.resolve(v);
      continue;
    }

    if (a === "--exclude") {
      const v = argv[++i];
      if (!v) throw new Error("Missing value for --exclude");
      args.excludeSegments.add(v.toLowerCase());
      continue;
    }

    if (a === "--ext") {
      const v = argv[++i];
      if (!v) throw new Error("Missing value for --ext");
      args.allowExt = new Set(parseExtList(v));
      continue;
    }

    if (a === "--max-bytes") {
      const v = argv[++i];
      if (!v) throw new Error("Missing value for --max-bytes");
      const n = Number(v);
      if (!Number.isFinite(n) || n < 0) throw new Error("Invalid --max-bytes");
      args.maxBytes = n;
      continue;
    }

    throw new Error(`Unknown arg: ${a}`);
  }

  return args;
}

function printHelp() {
  const msg = `
Usage:
  node tools/mojibake_scan.js [--root <path>] [--exclude <segment> ...] [--ext <list>] [--max-bytes <n>]

Options:
  --root <path>         Repo root (default: cwd)
  --exclude <segment>   Exclude a path segment or prefix (repeatable)
  --ext <list>          Allowed extensions, comma-separated (default: ${DEFAULT_ALLOW_EXT.join(",")})
  --max-bytes <n>       Skip files larger than n bytes (default: 2097152)
  -h, --help            Show help
`.trim();
  process.stdout.write(msg + "\n");
}

function shouldExclude(relPosixPath, excludeSegmentsSet) {
  const relLower = relPosixPath.toLowerCase();

  // segment-based check (safer than substring tricks)
  const segs = relLower.split("/").filter(Boolean);

  for (const ex of excludeSegmentsSet) {
    const exLower = ex.toLowerCase();

    // Allow both:
    // 1) exact segment match (e.g. "node_modules")
    // 2) prefix path match (e.g. "server/scripts")
    if (exLower.includes("/")) {
      if (relLower === exLower || relLower.startsWith(exLower + "/")) return true;
      continue;
    }

    if (segs.includes(exLower)) return true;
  }

  return false;
}

function listFilesDeterministic(rootAbs, allowExt, excludeSegmentsSet, maxBytes) {
  const out = [];

  function walk(dirAbs) {
    let entries;
    try {
      entries = fs.readdirSync(dirAbs, { withFileTypes: true });
    } catch {
      return;
    }

    entries.sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0));

    for (const ent of entries) {
      const abs = path.join(dirAbs, ent.name);
      const rel = relPosix(rootAbs, abs);
      if (!rel || rel.startsWith("..")) continue;

      if (shouldExclude(rel, excludeSegmentsSet)) continue;

      // symlinks: skip to avoid loops
      if (ent.isSymbolicLink()) continue;

      if (ent.isDirectory()) {
        walk(abs);
        continue;
      }

      if (!ent.isFile()) continue;

      const ext = path.extname(ent.name).toLowerCase();
      if (!allowExt.has(ext)) continue;

      // size guard
      try {
        const st = fs.statSync(abs);
        if (maxBytes > 0 && st.size > maxBytes) continue;
      } catch {
        continue;
      }

      out.push(abs);
    }
  }

  walk(rootAbs);

  // final deterministic sort by relative path
  out.sort((a, b) => {
    const ra = relPosix(rootAbs, a);
    const rb = relPosix(rootAbs, b);
    return ra < rb ? -1 : ra > rb ? 1 : 0;
  });

  return out;
}

function truncate(s, max) {
  return s.length <= max ? s : s.slice(0, max - 1) + "…";
}

function sanitizeSnippet(line) {
  return truncate(
    line.replace(/\t/g, " ").replace(/\r?\n$/, ""),
    200
  );
}

function findAllMatches(line, regex) {
  const matches = [];
  regex.lastIndex = 0;
  let m;
  while ((m = regex.exec(line)) !== null) {
    matches.push({ index: m.index, match: m[0] });
    if (m.index === regex.lastIndex) regex.lastIndex++;
  }
  return matches;
}

function decodeUtf8Lossy(buf) {
  // strips UTF-8 BOM if present
  let s = decoder.decode(buf);
  if (s.charCodeAt(0) === 0xfeff) s = s.slice(1);
  return s;
}

function scanFile(rootAbs, fileAbs) {
  const rel = relPosix(rootAbs, fileAbs);

  let buf;
  try {
    buf = fs.readFileSync(fileAbs);
  } catch {
    return [];
  }

  const content = decodeUtf8Lossy(buf);

  // split robustly
  const lines = content.split("\n");
  const records = [];

  // Mojibake patterns (common UTF-8->Latin1 artifacts)
  const mojibakeRegex = /Ã[\u0080-\u00BF]|Â[\u0080-\u00BF]|â[\u0080-\u00BF]/g;

  // Unicode replacement char
  const replacementRegex = /\uFFFD/g;

  for (let i = 0; i < lines.length; i++) {
    const lineText = lines[i];

    for (const mm of findAllMatches(lineText, replacementRegex)) {
      records.push({
        path: rel,
        line: i + 1,
        col: mm.index + 1,
        kind: "replacement_char",
        match: "\uFFFD",
        snippet: sanitizeSnippet(lineText),
      });
    }

    for (const mm of findAllMatches(lineText, mojibakeRegex)) {
      records.push({
        path: rel,
        line: i + 1,
        col: mm.index + 1,
        kind: "mojibake",
        match: truncate(mm.match, 32),
        snippet: sanitizeSnippet(lineText),
      });
    }
  }

  return records;
}

function sortRecords(records) {
  records.sort((a, b) => {
    if (a.path !== b.path) return a.path < b.path ? -1 : 1;
    if (a.line !== b.line) return a.line - b.line;
    if (a.col !== b.col) return a.col - b.col;
    if (a.kind !== b.kind) return a.kind < b.kind ? -1 : 1;
    if (a.match !== b.match) return a.match < b.match ? -1 : 1;
    return 0;
  });
  return records;
}

function main() {
  try {
    const args = parseArgs(process.argv);

    if (args.help) {
      printHelp();
      process.exit(0);
      return;
    }

    const rootAbs = path.resolve(args.root);

    const files = listFilesDeterministic(
      rootAbs,
      args.allowExt,
      args.excludeSegments,
      args.maxBytes
    );

    let all = [];
    for (const f of files) all = all.concat(scanFile(rootAbs, f));

    sortRecords(all);

    for (const r of all) process.stdout.write(JSON.stringify(r) + "\n");

    process.exit(all.length > 0 ? 1 : 0);
  } catch (e) {
    process.stderr.write(String(e && e.stack ? e.stack : e) + "\n");
    process.exit(2);
  }
}

main();
