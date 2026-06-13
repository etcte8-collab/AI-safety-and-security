#!/usr/bin/env bash
# deploy_to_github.sh
# ─────────────────────────────────────────────────────────────────────────────
# One-shot script: clones your repo, copies the loop-engineering project
# into src/loop_engineering/, commits, and pushes.
#
# Usage:
#   chmod +x deploy_to_github.sh
#   ./deploy_to_github.sh
#
# Requirements:
#   - git configured with credentials for etcte8-collab (SSH key or HTTPS token)
#   - This script run from the loop-engineering/ project root
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

REPO_URL="https://github.com/etcte8-collab/AI-safety-and-security.git"
TARGET_SUBDIR="src/loop_engineering"
BRANCH="main"
COMMIT_MSG="feat: add Loop Engineering prompt injection red-team agent

- 4-layer loop: Generator → Attacker → Evaluator → RetryJudge
- Fully local — runs on Ollama (Qwen3.6, Llama3, Mistral, etc.)
- Harness eval suite across 4 AI security scenarios  
- Rich CLI with loop trace JSON output
- Demonstrates loop engineering + harness engineering patterns"

# ── Temp clone ──────────────────────────────────────────────────────────────
TMPDIR=$(mktemp -d)
echo "📥 Cloning repo..."
git clone "$REPO_URL" "$TMPDIR/repo"

# ── Copy project files ───────────────────────────────────────────────────────
DEST="$TMPDIR/repo/$TARGET_SUBDIR"
mkdir -p "$DEST"

echo "📁 Copying project files..."
# Copy from the loop-engineering directory (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cp -r "$SCRIPT_DIR/src/"* "$DEST/"
cp "$SCRIPT_DIR/requirements.txt" "$DEST/"
cp "$SCRIPT_DIR/README.md" "$DEST/"
cp "$SCRIPT_DIR/.env.example" "$DEST/"
cp "$SCRIPT_DIR/.gitignore" "$DEST/loop_engineering.gitignore"

# ── Commit and push ──────────────────────────────────────────────────────────
cd "$TMPDIR/repo"
git add "$TARGET_SUBDIR"
git status

echo ""
echo "📝 Committing..."
git commit -m "$COMMIT_MSG"

echo "🚀 Pushing to $BRANCH..."
git push origin "$BRANCH"

# ── Cleanup ───────────────────────────────────────────────────────────────────
rm -rf "$TMPDIR"

echo ""
echo "✅ Done! Files are now at:"
echo "   https://github.com/etcte8-collab/AI-safety-and-security/tree/main/$TARGET_SUBDIR"
