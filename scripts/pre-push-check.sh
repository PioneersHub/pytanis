#!/bin/bash
# Pre-push verification script for pytanis
# This ensures all code quality checks pass before pushing to remote

set -e  # Exit on any error

echo "================================================"
echo "Running pre-push checks..."
echo "================================================"

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --staged --quiet; then
    echo "⚠️  Warning: You have uncommitted changes. These will be included in the checks."
    echo ""
fi

# 1. Run pre-commit on all files (includes security checks)
echo ""
echo "1. Running pre-commit hooks (including security checks)..."
echo "------------------------------------------------"
pre-commit run --all-files
PRE_COMMIT_EXIT=$?

# Check if files were modified by pre-commit
if ! git diff --quiet; then
    echo ""
    echo "⚠️  Pre-commit hooks modified files. Please review and commit the changes:"
    git diff --name-only
    echo ""
    echo "Run 'git add -u && git commit -m \"style: apply pre-commit fixes\"' to commit the changes."
    exit 1
fi

if [ $PRE_COMMIT_EXIT -ne 0 ]; then
    echo "❌ Pre-commit hooks failed! Please fix the issues and try again."
    exit 1
fi
echo "✅ Pre-commit hooks passed!"

# 2. Run linting
echo ""
echo "2. Running linting (ruff, mypy, notebook checks)..."
echo "------------------------------------------------"
hatch run lint:all
if [ $? -ne 0 ]; then
    echo "❌ Linting failed! Please fix the issues and try again."
    exit 1
fi
echo "✅ Linting passed!"

# 3. Run tests to ensure linting didn't break anything
echo ""
echo "3. Running tests..."
echo "------------------------------------------------"
hatch run no-cov
if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Please fix the issues and try again."
    exit 1
fi
echo "✅ Tests passed!"

echo ""
echo "================================================"
echo "✅ All pre-push checks passed! Ready to push."
echo "================================================"
