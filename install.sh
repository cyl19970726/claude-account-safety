#!/usr/bin/env bash
set -eu

SKILL_NAME="claude-account-safety"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET=""
FORCE=0
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: ./install.sh [options]

Options:
  --target DIR   Install into DIR/claude-account-safety (DIR is a skills root)
  --project DIR  Install into DIR/.agents/skills/claude-account-safety
  --force        Back up an existing target, then replace it
  --dry-run      Print what would happen, change nothing
  -h, --help     Show this help

Examples:
  ./install.sh --target "$HOME/.agents/skills"
  ./install.sh --project .

No sudo. No network. Does not touch credentials or proxy configs.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      [ "$#" -ge 2 ] || { echo "missing value for --target" >&2; exit 2; }
      TARGET="$2"; shift 2 ;;
    --project)
      [ "$#" -ge 2 ] || { echo "missing value for --project" >&2; exit 2; }
      TARGET="$2/.agents/skills"; shift 2 ;;
    --force)
      FORCE=1; shift ;;
    --dry-run)
      DRY_RUN=1; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [ -z "$TARGET" ]; then
  TARGET="./.agents/skills"
fi

case "$(basename "$TARGET")" in
  "$SKILL_NAME") DEST="$TARGET" ;;
  *) DEST="$TARGET/$SKILL_NAME" ;;
esac

if [ ! -f "$SOURCE_DIR/SKILL.md" ]; then
  echo "error: SKILL.md not found in $SOURCE_DIR" >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  echo "secret scan: $SOURCE_DIR"
  if ! python3 "$SOURCE_DIR/scripts/secret_check.py" --root "$SOURCE_DIR"; then
    echo "error: secret-like content found; refusing to install." >&2
    echo "Move real links/tokens to a password manager and keep only op:// / env: / keychain: references." >&2
    exit 1
  fi
else
  echo "warning: python3 not found; skipping secret scan." >&2
fi

echo "source: $SOURCE_DIR"
echo "dest:   $DEST"

if [ -e "$DEST" ]; then
  if [ "$FORCE" -ne 1 ]; then
    echo "error: target exists. Re-run with --force to back it up and replace." >&2
    exit 1
  fi
  BACKUP="${DEST}.bak-$(date +%Y%m%d-%H%M%S)"
  echo "backup: $BACKUP"
  if [ "$DRY_RUN" -eq 0 ]; then
    mv "$DEST" "$BACKUP"
  fi
fi

if [ "$DRY_RUN" -eq 1 ]; then
  echo "[dry-run] would copy $SOURCE_DIR -> $DEST"
  exit 0
fi

mkdir -p "$(dirname "$DEST")"
mkdir -p "$DEST"
(
  cd "$SOURCE_DIR"
  LC_ALL=C tar -cf - \
    --exclude='./dist' \
    --exclude='./.git' \
    --exclude='*/__pycache__' \
    --exclude='*.pyc' \
    --exclude='./secrets.env' \
    --exclude='./machine-profile.json' \
    --exclude='./egress.json' \
    --exclude='./setup-report.md' \
    --exclude='./clash/profile.yaml' \
    .
) | (
  cd "$DEST"
  LC_ALL=C tar -xf -
)

if [ ! -f "$DEST/SKILL.md" ]; then
  echo "error: install verification failed; $DEST/SKILL.md missing" >&2
  exit 1
fi

echo "installed: $DEST"
echo
echo "Next:"
echo "  python3 \"$DEST/scripts/doctor.py\" --summary"
echo "  Read \"$DEST/references/09-new-machine.md\""
echo "  Invoke the skill from your agent (e.g. \$claude-account-safety)."
