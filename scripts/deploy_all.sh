#!/usr/bin/env bash
# Full YTM deploy: build frontend, protect static assets, clean, copy, deploy.
# Run as a SINGLE command so /deploy needs only one approval.
# No `set -e`: failures are handled explicitly so step 2's non-fatal warnings
# behave exactly as before, and every hard failure reports which step died.
set -uo pipefail

ROOT=/c/Users/robho/Documents/VAULT/TrainingMonkey-Clean

fail() { echo "DEPLOY FAILED at $1" >&2; exit 1; }

echo "=== Step 1: Build React frontend ==="
cd "$ROOT/frontend"            || fail "step 1 (cd frontend)"
npm run build                  || fail "step 1 (npm run build)"

echo "=== Step 2: Protect non-build static assets ==="
mkdir -p "$ROOT/protected_static"
for pair in "css/getting_started.css" "js/getting_started.js"; do
  sub="${pair%%/*}"; file="${pair##*/}"
  live="$ROOT/app/static/$sub/$file"
  backup="$ROOT/protected_static/$file"
  if [ -s "$live" ]; then
    cp -f "$live" "$backup" && echo "protected_static: refreshed $file from live"
  elif [ -s "$backup" ]; then
    cp -f "$backup" "$live" && echo "protected_static: WARNING live $file missing/empty — restored from backup"
  else
    echo "protected_static: ERROR both live and backup missing for $file — recover from git commit 27889ae" >&2
  fi
done

echo "=== Step 3: Clean stale build artifacts ==="
rm -f "$ROOT"/app/static/js/main.*.js \
      "$ROOT"/app/static/js/main.*.js.LICENSE.txt \
      "$ROOT"/app/static/css/main.*.css \
      "$ROOT"/app/build/static/js/main.*.js \
      "$ROOT"/app/build/static/js/main.*.js.LICENSE.txt \
      "$ROOT"/app/build/static/css/main.*.css

echo "=== Step 4: Copy build artifacts ==="
cp -r "$ROOT/frontend/build/."        "$ROOT/app/build/"  || fail "step 4 (copy build)"
cp -r "$ROOT/frontend/build/static/." "$ROOT/app/static/" || fail "step 4 (copy static)"

echo "=== Step 5: Deploy ==="
cd "$ROOT/app" || fail "step 5 (cd app)"
echo "" | cmd //c "C:\\Users\\robho\\Documents\\VAULT\\TrainingMonkey-Clean\\app\\deploy_strava_simple.bat" \
  || fail "step 5 (deploy_strava_simple.bat)"

echo "=== Deploy complete ==="
