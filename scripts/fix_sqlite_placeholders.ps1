# PowerShell script to fix SQLite placeholders in Python files
# Converts ? placeholders to %s for PostgreSQL

param(
    [string]$FilePath = "app/strava_app.py"
)

Write-Host "🔧 Fixing SQLite placeholders in $FilePath..."

# Read the file content
$content = Get-Content $FilePath -Raw

# Common SQLite placeholder patterns to fix
$replacements = @{
    'WHERE id = \?' = 'WHERE id = %s'
    'WHERE user_id = \?' = 'WHERE user_id = %s'
    'WHERE activity_id = \?' = 'WHERE activity_id = %s'
    'WHERE date = \?' = 'WHERE date = %s'
    'WHERE user_id = \? AND' = 'WHERE user_id = %s AND'
    'WHERE id = \? AND' = 'WHERE id = %s AND'
    'WHERE activity_id = \? AND' = 'WHERE activity_id = %s AND'
    'WHERE date = \? AND' = 'WHERE date = %s AND'
    'VALUES \(\?' = 'VALUES (%s'
    'VALUES \(.*\?' = 'VALUES (%s'
    'SET .* = \?' = 'SET %s = %s'
    'AND user_id = \?' = 'AND user_id = %s'
    'AND id = \?' = 'AND id = %s'
    'AND activity_id = \?' = 'AND activity_id = %s'
    'AND date = \?' = 'AND date = %s'
    'ORDER BY .* \?' = 'ORDER BY %s'
    'LIMIT \?' = 'LIMIT %s'
    'BETWEEN \? AND \?' = 'BETWEEN %s AND %s'
}

# Apply replacements
foreach ($pattern in $replacements.Keys) {
    $replacement = $replacements[$pattern]
    $oldContent = $content
    $content = $content -replace $pattern, $replacement
    
    if ($content -ne $oldContent) {
        Write-Host "✅ Fixed pattern: $pattern"
    }
}

# Write the updated content back
Set-Content $FilePath $content -NoNewline

Write-Host "🎉 SQLite placeholder fixes applied to $FilePath"
Write-Host "📋 Run validation to check results: python scripts/validate_sql_syntax.py"
