#!/usr/bin/env bash
# Usage:
#   ./release.sh                        # interactive — prompts for version + notes
#   ./release.sh v1.2.3 "notes here"   # fully non-interactive (Claude's mode)
set -euo pipefail

# ── Colour helpers ────────────────────────────────────────────────────────────
green() { printf '\033[32m%s\033[0m\n' "$*"; }
blue()  { printf '\033[34m%s\033[0m\n' "$*"; }
red()   { printf '\033[31m%s\033[0m\n' "$*"; exit 1; }

# ── Determine latest tag ──────────────────────────────────────────────────────
LATEST=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
VERSION_NUM="${LATEST#v}"
IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION_NUM"
SUGGESTED="v${MAJOR}.${MINOR}.$((PATCH + 1))"

# ── Version ───────────────────────────────────────────────────────────────────
VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
    blue "Latest tag: $LATEST  →  suggested next: $SUGGESTED"
    read -rp "Version [$SUGGESTED]: " VERSION
    VERSION="${VERSION:-$SUGGESTED}"
fi
[[ "$VERSION" != v* ]] && VERSION="v$VERSION"

# Guard: tag must not already exist
git rev-parse "$VERSION" &>/dev/null && red "Tag $VERSION already exists."

# ── Release notes ─────────────────────────────────────────────────────────────
NOTES="${2:-}"
if [[ -z "$NOTES" ]]; then
    AUTO=$(git log "${LATEST}..HEAD" --oneline --no-decorate 2>/dev/null | sed 's/^/- /')
    [[ -z "$AUTO" ]] && AUTO="- No commits since $LATEST"
    blue "Commits since $LATEST:"
    echo "$AUTO"
    echo ""
    read -rp "Use these as release notes? [Y/n]: " USE
    if [[ "${USE:-Y}" =~ ^[Nn]$ ]]; then
        read -rp "Notes: " NOTES
    else
        NOTES="$AUTO"
    fi
fi

# ── Confirm ───────────────────────────────────────────────────────────────────
echo ""
blue "About to release:"
echo "  Tag   : $VERSION"
echo "  Notes : $NOTES"
echo ""
# Skip confirm prompt when both args supplied (non-interactive mode)
if [[ $# -lt 2 ]]; then
    read -rp "Proceed? [Y/n]: " OK
    [[ "${OK:-Y}" =~ ^[Nn]$ ]] && { echo "Aborted."; exit 0; }
fi

# ── Tests ─────────────────────────────────────────────────────────────────────
echo ""
blue "→ Running tests..."
python3 -m pytest lambda/test_handler.py -v --tb=short || red "Tests failed — release aborted."

# ── Tag & push ────────────────────────────────────────────────────────────────
echo ""
blue "→ Tagging $VERSION..."
git tag -a "$VERSION" -m "$NOTES"
git push origin "$VERSION"

# ── GitHub release ────────────────────────────────────────────────────────────
blue "→ Creating GitHub release..."
gh release create "$VERSION" \
    --title "$VERSION" \
    --notes "$NOTES"

echo ""
green "✓ Released $VERSION"
