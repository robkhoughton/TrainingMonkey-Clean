# Cursor Chat History Search Tool
# Search chat history by date range and keywords

param(
    [string]$Keyword = "",
    [string]$StartDate = "",
    [string]$EndDate = "",
    [int]$Days = 30,
    [switch]$ShowContent = $false,
    [switch]$ShowCode = $false
)

$HistoryPath = "$env:APPDATA\Cursor\User\History"

# Date filtering
if ($StartDate) {
    $StartDateObj = [DateTime]::Parse($StartDate)
} else {
    $StartDateObj = (Get-Date).AddDays(-$Days)
}

if ($EndDate) {
    $EndDateObj = [DateTime]::Parse($EndDate)
} else {
    $EndDateObj = Get-Date
}

Write-Host "=== Cursor Chat History Search ===" -ForegroundColor Green
Write-Host "Searching from: $($StartDateObj.ToString('yyyy-MM-dd')) to $($EndDateObj.ToString('yyyy-MM-dd'))" -ForegroundColor Yellow
if ($Keyword) { Write-Host "Keyword: '$Keyword'" -ForegroundColor Yellow }
Write-Host ""

$Results = @()
$TotalMatches = 0

# Get all conversation folders
$Conversations = Get-ChildItem $HistoryPath -Directory | 
    Where-Object { $_.LastWriteTime -ge $StartDateObj -and $_.LastWriteTime -le $EndDateObj } |
    Sort-Object LastWriteTime -Descending

foreach ($conv in $Conversations) {
    $entriesFile = Join-Path $conv.FullName "entries.json"
    
    if (Test-Path $entriesFile) {
        try {
            $entries = Get-Content $entriesFile | ConvertFrom-Json
            $resource = $entries.resource -replace "file:///", "" -replace "%3A", ":"
            $resource = [System.Web.HttpUtility]::UrlDecode($resource)
            
            $Matches = @()
            
            # Search in all files in the conversation
            $AllFiles = Get-ChildItem $conv.FullName -File
            
            foreach ($file in $AllFiles) {
                if ($Keyword) {
                    try {
                        $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
                        if ($content -and $content -match $Keyword) {
                            $Matches += @{
                                File = $file.Name
                                Type = $file.Extension
                                Matches = ($content | Select-String -Pattern $Keyword -AllMatches).Matches.Count
                            }
                            
                            if ($ShowContent) {
                                $lines = $content -split "`n"
                                $matchingLines = $lines | Select-String -Pattern $Keyword -Context 2
                                $Matches[-1].Context = $matchingLines
                            }
                        }
                    }
                    catch {
                        # Skip files that can't be read
                    }
                } else {
                    # If no keyword, just count files
                    $Matches += @{
                        File = $file.Name
                        Type = $file.Extension
                        Matches = 1
                    }
                }
            }
            
            if ($Matches.Count -gt 0) {
                $TotalMatches += $Matches.Count
                
                $Results += @{
                    ConversationId = $conv.Name
                    Date = $conv.LastWriteTime
                    Resource = $resource
                    FileCount = $AllFiles.Count
                    Matches = $Matches
                }
            }
        }
        catch {
            Write-Host "Error reading conversation $($conv.Name): $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Display results
Write-Host "Found $($Results.Count) conversations with $TotalMatches total matches" -ForegroundColor Cyan
Write-Host ""

foreach ($result in $Results) {
    Write-Host "📁 $($result.ConversationId)" -ForegroundColor White
    Write-Host "   📅 $($result.Date.ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor Gray
    Write-Host "   📄 $($result.Resource)" -ForegroundColor Gray
    Write-Host "   📊 $($result.Matches.Count) matching files" -ForegroundColor Gray
    
    if ($Keyword) {
        foreach ($match in $result.Matches) {
            Write-Host "      🔍 $($match.File) ($($match.Type)) - $($match.Matches) matches" -ForegroundColor Green
            
            if ($ShowContent -and $match.Context) {
                Write-Host "         Context:" -ForegroundColor Yellow
                foreach ($line in $match.Context) {
                    Write-Host "         $line" -ForegroundColor DarkYellow
                }
            }
        }
    }
    Write-Host ""
}

Write-Host "=== Usage Examples ===" -ForegroundColor Green
Write-Host ".\search_chat_history.ps1 -Keyword 'database' -Days 7" -ForegroundColor Yellow
Write-Host ".\search_chat_history.ps1 -Keyword 'error' -StartDate '2025-09-20' -EndDate '2025-09-22'" -ForegroundColor Yellow
Write-Host ".\search_chat_history.ps1 -Keyword 'function' -ShowContent -Days 3" -ForegroundColor Yellow
Write-Host ".\search_chat_history.ps1 -Days 1  # Show all conversations from today" -ForegroundColor Yellow
