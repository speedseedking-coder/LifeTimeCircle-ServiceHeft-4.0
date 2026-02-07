✅ PR #65 gemerged: `ci: actually run docs unified validator (root workdir)`
✅ CI Workflow (`.github/workflows/ci.yml`): Step **LTC docs unified validator** läuft aus Repo-Root (`working-directory: `${{ github.workspace }}`) und ruft `server/scripts/patch_docs_unified_final_refresh.ps1` auf
✅ Script hinzugefügt: `server/scripts/patch_ci_fix_docs_validator_step.ps1` (dedupe + workdir=root + run-line fix)
✅ CI grün auf `main`: **pytest** + Docs Unified Validator + Web Build (`packages/web`)
