#!/usr/bin/env bash
set -eu

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="$(cat "$SOURCE_DIR/VERSION")"
OUT="${1:-$SOURCE_DIR/dist/claude-account-safety-$VERSION.tar.gz}"

if ! python3 "$SOURCE_DIR/scripts/secret_check.py" --root "$SOURCE_DIR"; then
  echo "error: secret-like content found; refusing to package." >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
LC_ALL=C tar -czf "$OUT" \
  --exclude="$(basename "$SOURCE_DIR")/dist" \
  --exclude="$(basename "$SOURCE_DIR")/.git" \
  --exclude="*/__pycache__" \
  --exclude="*.pyc" \
  --exclude="*/.DS_Store" \
  --exclude="$(basename "$SOURCE_DIR")/secrets.env" \
  --exclude="$(basename "$SOURCE_DIR")/machine-profile.json" \
  --exclude="$(basename "$SOURCE_DIR")/egress.json" \
  --exclude="$(basename "$SOURCE_DIR")/setup-report.md" \
  --exclude="$(basename "$SOURCE_DIR")/clash/profile.yaml" \
  -C "$(dirname "$SOURCE_DIR")" "$(basename "$SOURCE_DIR")"

python3 - "$OUT" <<'PY'
import hashlib
import sys
from pathlib import Path

path = Path(sys.argv[1])
digest = hashlib.sha256(path.read_bytes()).hexdigest()
Path(str(path) + ".sha256").write_text(f"{digest}  {path.name}\n", encoding="utf-8")
PY

echo "package: $OUT"
echo "checksum: $OUT.sha256"
