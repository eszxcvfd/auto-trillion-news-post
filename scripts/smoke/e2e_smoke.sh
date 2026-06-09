#!/usr/bin/env bash
# Manual E2E smoke checks for the local Web UI operator surface.
# Usage: ./scripts/smoke/e2e_smoke.sh [base_url]
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8080}"
PASS=0
FAIL=0

check() {
  local name="$1"
  local cmd="$2"
  local expect="$3"
  local tmp
  tmp="$(mktemp)"
  echo "==> $name"
  if eval "$cmd" >"$tmp" && grep -Fq "$expect" "$tmp"; then
    echo "PASS: $name"
    PASS=$((PASS + 1))
  else
    echo "FAIL: $name"
    echo "Expected pattern: $expect"
    echo "Response snippet:"
    head -c 400 "$tmp" 2>/dev/null || true
    FAIL=$((FAIL + 1))
  fi
  rm -f "$tmp"
}

echo "E2E smoke against $BASE_URL"

# Best-effort cleanup so post-status checks start from a neutral state.
curl -fsS -X POST "$BASE_URL/api/post/skip" >/dev/null 2>&1 || true

check "root HTML loads" \
  "curl -fsS '$BASE_URL/'" \
  "Trillion News Auto Post"

check "api config" \
  "curl -fsS '$BASE_URL/api/config'" \
  "excel_file"

check "api workbooks list" \
  "curl -fsS '$BASE_URL/api/workbooks'" \
  "Trillion"

check "api workbook inspect" \
  "curl -fsS '$BASE_URL/api/workbook/inspect'" \
  "sheets"

check "api workbook inspect exposes eligible_platforms" \
  "curl -fsS '$BASE_URL/api/workbook/inspect'" \
  "eligible_platforms"

check "api posting plan" \
  "curl -fsS '$BASE_URL/api/plan?limit=2&platforms=linkedin,facebook,x,instagram,pinterest,threads,tiktok,youtube'" \
  "candidates"

check "api sessions status" \
  "curl -fsS '$BASE_URL/api/sessions/status'" \
  "linkedin"

check "api sessions includes B3 platforms" \
  "curl -fsS '$BASE_URL/api/sessions/status'" \
  "tiktok"

check "api post status inactive by default" \
  "curl -fsS '$BASE_URL/api/post/status'" \
  '"active":false'

check "api scheduler schedules" \
  "curl -fsS '$BASE_URL/api/schedules'" \
  "job_type"

check "api scheduler history" \
  "curl -fsS '$BASE_URL/api/history?limit=5'" \
  "[]"

echo ""
echo "Smoke summary: $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
  exit 1
fi