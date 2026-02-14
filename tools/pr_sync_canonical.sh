#!/usr/bin/env bash
set -euo pipefail

BASE="origin/main"
BRANCH="chore/pr-sync-canonical-scripts"
REMOTE="origin"
REPO_URL="https://github.com/speedseedking-coder/LifeTimeCircle-ServiceHeft-4.0.git"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base|--base-ref) BASE="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --remote) REMOTE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

cd "$(git rev-parse --show-toplevel)"

git remote set-url "$REMOTE" "$REPO_URL" 2>/dev/null || git remote add "$REMOTE" "$REPO_URL"
git fetch "$REMOTE" --prune --tags >/dev/null

TOKEN="${LTC_GH_TOKEN:-${GH_TOKEN:-${GITHUB_TOKEN:-}}}"
if [[ -z "${TOKEN}" ]]; then echo "STOP(AUTH): TOKEN_MISSING"; exit 0; fi
if [[ "${#TOKEN}" -lt 16 ]]; then echo "STOP(AUTH): TOKEN_TOO_SHORT"; exit 0; fi
if echo "$TOKEN" | grep -Eq 'DEIN_TOKEN|NICHT_LOGGEN|PASTE_REAL_TOKEN_HERE|YOUR_TOKEN|TOKEN_HERE|<|>'; then
  echo "STOP(AUTH): TOKEN_PLACEHOLDER"; exit 0
fi

ASKPASS="$(mktemp -t ltc_askpass.XXXXXX)"
cat >"$ASKPASS" <<'EOF'
#!/usr/bin/env sh
case "$1" in
  *Username*|*username*) echo "x-access-token" ;;
  *) printf '%s\n' "$LTC_ASKPASS_TOKEN" ;;
esac
EOF
chmod +x "$ASKPASS"

export LTC_ASKPASS_TOKEN="$TOKEN"
export GIT_ASKPASS="$ASKPASS"
export GIT_TERMINAL_PROMPT=0

git checkout -B "$BRANCH" "$BASE"
git -c credential.helper= push --force-with-lease "$REMOTE" "HEAD:$BRANCH"
echo "PR: https://github.com/speedseedking-coder/LifeTimeCircle-ServiceHeft-4.0/compare/main...${BRANCH}?expand=1"

rm -f "$ASKPASS"
unset LTC_ASKPASS_TOKEN GIT_ASKPASS GIT_TERMINAL_PROMPT
