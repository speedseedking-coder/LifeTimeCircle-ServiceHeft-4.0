#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const ALLOW_EXT = new Set([".md", ".ts", ".tsx", ".js", ".py"]);
const DEFAULT_EXCLUDE_SEGMENTS = [
  ".git",
  "node_modules",
  "dist",
  "server/scripts",
  "tools",
  "server/data",
  "server/storage",
  "packages/web/dist",
  "packages/web/node_modules",
  "packages/web/.vite",
].map((s) => s.toLowerCase());

function toPosix(p) { return p.split(path.sep).join("/"); }
function relPosix(root, abs) { return toPosix(path.relative(root, abs)).replace(/^(\.\/)+/, ""); }

function hasExcludedSegment(relLower) {
  for (const seg of DEFAULT_EXCLUDE_SEGMENTS) {
    if (relLower === seg || relLower.startsWith(seg + "/") || relLower.includes("/" + seg + "/") || relLower.endsWith("/" + seg)) return true;
  }
  return false;
}

function listFilesDeterministic(rootAbs) {
  const out = [];
  function walk(dirAbs) {
    let entries = fs.readdirSync(dirAbs, { withFileTypes: true });
    entries.sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0));
    for (const ent of entries) {
      const abs = path.join(dirAbs, ent.name);
      const rel = relPosix(rootAbs, abs);
      const relLower = rel.toLowerCase();
      if (hasExcludedSegment(relLower)) continue;

      if (ent.isDirectory()) walk(abs);
      else if (ent.isFile()) {
        const ext = path.extname(ent.name).toLowerCase();
        if (!ALLOW_EXT.has(ext)) continue;
        out.push(abs);
      }
    }
  }
  walk(rootAbs);
  out.sort((a, b) => {
    const ra = relPosix(rootAbs, a);
    const rb = relPosix(rootAbs, b);
    return ra < rb ? -1 : ra > rb ? 1 : 0;
  });
  return out;
}

function truncate(s, max) { return s.length <= max ? s : (s.slice(0, max - 1) + "…"); }
function sanitizeSnippet(line) { return truncate(line.replace(/\t/g, " ").replace(/\r?\n$/, ""), 200); }

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

function scanFile(rootAbs, fileAbs) {
  const rel = relPosix(rootAbs, fileAbs);
  const content = fs.readFileSync(fileAbs, { encoding: "utf8" });
  const lines = content.split("\n");
  const records = [];

  const mojibakeRegex = /Ã[\u0080-\u00BF]|Â[\u0080-\u00BF]|â[\u0080-\u00BF]/g;
  const replacementRegex = /\uFFFD/g;

  for (let i = 0; i < lines.length; i++) {
    const lineText = lines[i];

    for (const mm of findAllMatches(lineText, replacementRegex)) {
      records.push({ path: rel, line: i + 1, col: mm.index + 1, kind: "replacement_char", match: "�", snippet: sanitizeSnippet(lineText) });
    }
    for (const mm of findAllMatches(lineText, mojibakeRegex)) {
      records.push({ path: rel, line: i + 1, col: mm.index + 1, kind: "mojibake", match: truncate(mm.match, 32), snippet: sanitizeSnippet(lineText) });
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

function parseArgs(argv) {
  const args = { root: process.cwd() };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--root") args.root = path.resolve(argv[++i]);
    else if (a === "-h" || a === "--help") return { help: true, root: args.root };
    else throw new Error(`Unknown arg: ${a}`);
  }
  return args;
}

function main() {
  const args = parseArgs(process.argv);
  const rootAbs = path.resolve(args.root);
  const files = listFilesDeterministic(rootAbs);

  let all = [];
  for (const f of files) all = all.concat(scanFile(rootAbs, f));

  sortRecords(all);
  for (const r of all) process.stdout.write(JSON.stringify(r) + "\n");
  process.exit(all.length > 0 ? 1 : 0);
}

main();