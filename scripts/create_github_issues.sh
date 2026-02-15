#!/bin/bash
# Create GitHub issues from generated markdown files
# Requires GitHub CLI (gh) to be installed and authenticated

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed"
    echo "Install from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub CLI"
    echo "Run: gh auth login"
    exit 1
fi

echo "Creating GitHub issues from .github/issues/*.md"
echo "================================================"
echo ""

# Counter
created=0
failed=0

# Loop through all issue files
for file in .github/issues/task-*.md; do
    if [ -f "$file" ]; then
        # Extract title from file
        title=$(grep '^title:' "$file" | sed 's/title: "\(.*\)"/\1/')
        
        # Extract labels
        labels=$(grep '^labels:' "$file" | sed 's/labels: //')
        
        echo "Creating issue: $title"
        
        # Create issue
        if gh issue create --title "$title" --body-file "$file" --label "$labels"; then
            ((created++))
            echo "  ✓ Created"
        else
            ((failed++))
            echo "  ✗ Failed"
        fi
        
        echo ""
        
        # Rate limiting - wait 1 second between issues
        sleep 1
    fi
done

echo "================================================"
echo "Summary:"
echo "  Created: $created issues"
echo "  Failed: $failed issues"
echo "================================================"
