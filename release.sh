#!/bin/bash
set -e

VERSION=$(grep '^version' pyproject.toml | cut -d'"' -f2)

if [ -z "$VERSION" ]; then
    echo "Could not extract version from pyproject.toml"
    exit 1
fi

echo "Releasing v$VERSION"

# Ensure we're on master and up to date
git diff --quiet || { echo "Uncommitted changes"; exit 1; }
git push

# Create release (triggers GitHub Actions for PyPI publish)
gh release create "v$VERSION" --generate-notes

echo "Released v$VERSION"
echo "GitHub Actions will publish to PyPI"
