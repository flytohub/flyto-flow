#!/bin/bash
# Sync baseline translations from flyto-i18n dist into frontend bundle.
# Run this after updating translations in flyto-i18n.
#
# Usage: bash scripts/sync-i18n.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$(dirname "$SCRIPT_DIR")"
I18N_DIST="$FRONTEND_DIR/../../../../../flyto-i18n/dist/cloud"
BUNDLED_DIR="$FRONTEND_DIR/src/i18n/bundled"

if [ ! -d "$I18N_DIST" ]; then
  echo "flyto-i18n dist not found at: $I18N_DIST"
  echo "Make sure flyto-i18n is cloned alongside flyto-cloud and dist is built."
  exit 1
fi

mkdir -p "$BUNDLED_DIR"

# Extract version + translations only (skip metadata)
python3 -c "
import json, sys, os

src = '$I18N_DIST'
dst = '$BUNDLED_DIR'

for locale in ['en', 'zh-TW']:
    path = f'{src}/{locale}.json'
    if not os.path.exists(path):
        print(f'  SKIP {locale}.json (not found)')
        continue
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    bundled = {'version': data['version'], 'translations': data['translations']}
    out = f'{dst}/{locale}.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(bundled, f, ensure_ascii=False)
    size = os.path.getsize(out) // 1024
    print(f'  {locale}.json: {size}K (v{data[\"version\"]})')
"

echo "Baseline translations synced to src/i18n/bundled/"
