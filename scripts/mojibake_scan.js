#!/usr/bin/env node
/**
 * LifeTimeCircle – Mojibake / Encoding Gate
 * Robust gegen ENOBUFS: erst Dateiliste (files-with-matches), dann pro Datei max 1 Treffer.
 * WICHTIG: stderr wird getrennt behandelt (keine "Dateiliste" aus Fehlermeldungen).
 */
const { spawnSync } = require("node:child_process");

// Typische UTF-8->Latin1 Mojibake Sequenzen + kaputte Typo-Zeichen
const PATTERNS = [
  "fÃ¼","Ã¼","Ã¤","Ã¶","ÃŸ","Ã„","Ã–","Ãœ",
  "â€“","â€”","â€ž","â€œ","â€\u009D","â€\u0098","â€\u0099","â€¦",
  "Â ", "Â·", "Â°",
  "ÔÇ", "â”œ", "Ã”Ã‡", "Ã¥Ã†", "Ã¥Ã‰",
  "�"
];

const INCLUDE_GLOBS = [
  "**/*.md","**/*.txt","**/*.json","**/*.yml","**/*.yaml",
  "**/*.py","**/*.ps1","**/*.sh",
  "**/*.ts","**/*.tsx","**/*.js","**/*.jsx",
  "**/*.css","**/*.html"
];

const EXCLUDE_GLOBS = [
  "!**/node_modules/**",
  "!**/dist/**",
  "!**/.git/**",
  "!**/.pytest_cache/**",
  "!**/test-results/**",
  "!server/data/**",
  "!server/storage/**",
  "!packages/**/package-lock.json",
  "!packages/**/pnpm-lock.yaml",
  "!packages/**/yarn.lock",
  "!scripts/mojibake_scan.js",
  "!scripts/quick_check.ps1"
];

const RG_BASE = ["--hidden", "--no-ignore-vcs", "--no-messages"];

function runRg(args) {
  const res = spawnSync("rg", args, {
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024
  });
  return {
    error: res.error || null,
    status: typeof res.status === "number" ? res.status : 2,
    stdout: res.stdout || "",
    stderr: res.stderr || ""
  };
}

function filesWithMatches() {
  const args = [...RG_BASE, "--files-with-matches"];

  for (const g of INCLUDE_GLOBS) args.push("-g", g);
  for (const g of EXCLUDE_GLOBS) args.push("-g", g);
  for (const p of PATTERNS) args.push("-e", p);

  args.push(".");

  const r = runRg(args);
  if (r.error) {
    console.error(`ERROR: rg spawn failed: ${r.error.message}`);
    process.exit(2);
  }
  if (r.stderr.trim()) {
    console.error(`ERROR: rg stderr:\n${r.stderr.trim()}`);
    process.exit(2);
  }
  if (r.status === 1) return []; // no matches
  if (r.status !== 0) {
    console.error((r.stdout || "").trim() || `ERROR: rg exited with code ${r.status}`);
    process.exit(r.status || 2);
  }

  return r.stdout.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
}

function firstMatchLine(file) {
  const args = [...RG_BASE, "-n", "-S", "-m", "1"];
  for (const p of PATTERNS) args.push("-e", p);
  args.push(file);

  const r = runRg(args);
  if (r.error) return `ERROR: rg failed on ${file}: ${r.error.message}`;
  if (r.stderr.trim()) return `ERROR: rg stderr on ${file}: ${r.stderr.trim()}`;
  if (r.status === 1) return null;
  if (r.status !== 0) return (r.stdout || "").trim() || `ERROR: rg exited ${r.status} on ${file}`;

  return (r.stdout || "").split(/\r?\n/).find(Boolean) || null;
}

(function main() {
  const files = filesWithMatches();

  if (files.length === 0) {
    console.log("OK: Mojibake scan clean (0 Treffer).");
    process.exit(0);
  }

  console.error("FAIL: Mojibake-Muster gefunden (max 50 Treffer):");
  let shown = 0;

  for (const f of files) {
    if (shown >= 50) break;
    const hit = firstMatchLine(f);
    if (hit) {
      console.error(` - ${hit}`);
      shown += 1;
    }
  }

  if (files.length > 50) console.error(` - ... ${files.length - 50} weitere Dateien mit Treffern`);
  process.exit(1);
})();