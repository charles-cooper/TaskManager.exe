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

echo "Release v$VERSION created, waiting for publish workflow..."

# Poll GitHub Actions workflow until it completes
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
for i in $(seq 1 60); do
    sleep 10
    RUN=$(gh run list --repo "$REPO" --workflow publish.yml --limit 1 --json status,conclusion,databaseId -q '.[0]')
    STATUS=$(echo "$RUN" | jq -r '.status')
    CONCLUSION=$(echo "$RUN" | jq -r '.conclusion')
    RUN_ID=$(echo "$RUN" | jq -r '.databaseId')
    echo "  [$i/60] Workflow run $RUN_ID: status=$STATUS conclusion=$CONCLUSION"
    if [ "$STATUS" = "completed" ]; then
        if [ "$CONCLUSION" = "success" ]; then
            echo "Publish workflow succeeded!"
            break
        else
            echo "Publish workflow failed (conclusion=$CONCLUSION)"
            echo "  https://github.com/$REPO/actions/runs/$RUN_ID"
            exit 1
        fi
    fi
done

if [ "$STATUS" != "completed" ]; then
    echo "Timed out waiting for publish workflow (10 minutes)"
    echo "  https://github.com/$REPO/actions/runs/$RUN_ID"
    exit 1
fi

# Poll PyPI until the package is available
echo "Waiting for PyPI to serve v$VERSION..."
PACKAGE="taskmanager-exe"
for i in $(seq 1 30); do
    sleep 10
    HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' "https://pypi.org/pypi/$PACKAGE/$VERSION/json")
    echo "  [$i/30] PyPI check: HTTP $HTTP_CODE"
    if [ "$HTTP_CODE" = "200" ]; then
        echo "v$VERSION is live on PyPI!"
        echo "  https://pypi.org/project/$PACKAGE/$VERSION/"
        exit 0
    fi
done

echo "Timed out waiting for PyPI availability (5 minutes)"
exit 1
