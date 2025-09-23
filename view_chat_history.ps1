# Cursor Chat History Viewer
# This script helps you browse and search your Cursor chat history

param(
    [string]$SearchTerm = "",
    [int]$Days = 7
)

$HistoryPath = "$env:APPDATA\Cursor\User\History"
$CutoffDate = (Get-Date).AddDays(-$Days)

Write-Host "=== Cursor Chat History Viewer ===" -ForegroundColor Green
Write-Host "Searching in: $HistoryPath" -ForegroundColor Yellow
Write-Host ""

# Get all conversation folders
$Conversations = Get-ChildItem $HistoryPath -Directory | 
    Where-Object { $_.LastWriteTime -gt $CutoffDate } |
    Sort-Object LastWriteTime -Descending

Write-Host "Found $($Conversations.Count) recent conversations:" -ForegroundColor Cyan
Write-Host ""

foreach ($conv in $Conversations) {
    $entriesFile = Join-Path $conv.FullName "entries.json"
    
    if (Test-Path $entriesFile) {
        try {
            $entries = Get-Content $entriesFile | ConvertFrom-Json
            $resource = $entries.resource -replace "file:///", "" -replace "%3A", ":"
            $resource = [System.Web.HttpUtility]::UrlDecode($resource)
            
            Write-Host "📁 $($conv.Name)" -ForegroundColor White
            Write-Host "   📅 $($conv.LastWriteTime)" -ForegroundColor Gray
            Write-Host "   📄 $($resource)" -ForegroundColor Gray
            Write-Host "   📊 $($entries.entries.Count) entries" -ForegroundColor Gray
            
            # Search in markdown files if search term provided
            if ($SearchTerm) {
                $mdFiles = Get-ChildItem $conv.FullName -Filter "*.md"
                foreach ($mdFile in $mdFiles) {
                    $content = Get-Content $mdFile.FullName -Raw
                    if ($content -match $SearchTerm) {
                        Write-Host "   🔍 Found '$SearchTerm' in $($mdFile.Name)" -ForegroundColor Green
                    }
                }
            }
            Write-Host ""
        }
        catch {
            Write-Host "   ❌ Error reading $($conv.Name)" -ForegroundColor Red
        }
    }
}

Write-Host "=== Usage Examples ===" -ForegroundColor Green
Write-Host ".\view_chat_history.ps1 -SearchTerm 'database' -Days 30" -ForegroundColor Yellow
Write-Host ".\view_chat_history.ps1 -Days 1  # Show only today's conversations" -ForegroundColor Yellow
