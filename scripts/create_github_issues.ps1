# PowerShell script to create GitHub issues from generated markdown files
# Requires GitHub CLI (gh) to be installed and authenticated

# Check if gh is installed
if (!(Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "Error: GitHub CLI (gh) is not installed" -ForegroundColor Red
    Write-Host "Install from: https://cli.github.com/"
    exit 1
}

# Check if authenticated
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Not authenticated with GitHub CLI" -ForegroundColor Red
    Write-Host "Run: gh auth login"
    exit 1
}

Write-Host "Creating GitHub issues from .github/issues/*.md" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Counters
$created = 0
$failed = 0

# Get all issue files
$issueFiles = Get-ChildItem -Path ".github/issues/task-*.md" | Sort-Object Name

foreach ($file in $issueFiles) {
    # Read file content
    $content = Get-Content $file.FullName -Raw
    
    # Extract title
    if ($content -match 'title: "([^"]+)"') {
        $title = $matches[1]
    } else {
        Write-Host "  Could not extract title from $($file.Name)" -ForegroundColor Red
        $failed++
        continue
    }
    
    # Extract labels
    $labelArgs = @()
    if ($content -match 'labels: (.+)') {
        $labelsRaw = $matches[1].Trim()
        # Split labels and add each one separately
        $labelList = $labelsRaw -split ',' | ForEach-Object { $_.Trim() }
        foreach ($label in $labelList) {
            $labelArgs += "--label"
            $labelArgs += $label
        }
    } else {
        $labelArgs = @("--label", "ai-agent", "--label", "enhancement")
    }
    
    Write-Host "Creating issue: $title" -ForegroundColor Yellow
    
    # Create issue
    try {
        $result = gh issue create --title $title --body-file $file.FullName @labelArgs 2>&1
        if ($LASTEXITCODE -eq 0) {
            $created++
            Write-Host "  Created: $result" -ForegroundColor Green
        } else {
            $failed++
            Write-Host "  Failed: $result" -ForegroundColor Red
        }
    } catch {
        $failed++
        Write-Host "  Failed: $_" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # Rate limiting - wait 1 second between issues
    Start-Sleep -Seconds 1
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Created: $created issues" -ForegroundColor Green
Write-Host "  Failed: $failed issues" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host "================================================" -ForegroundColor Cyan
