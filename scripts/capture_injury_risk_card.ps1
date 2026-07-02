# PowerShell script to capture screenshot of injury risk card
$url = "http://localhost:5001/dashboard?v=5"
$outputPath = Join-Path $PSScriptRoot "..\injury_risk_iteration4_full.png"

Write-Host "Opening Edge to capture screenshot..."
Write-Host "1. Navigate to: $url"
Write-Host "2. Close any modal dialogs"
Write-Host "3. Press F12 to open DevTools"
Write-Host "4. Run this in Console:"
Write-Host ""
Write-Host "// Find the injury risk card element"
Write-Host "const element = document.getElementById('at-a-glance-meters');"
Write-Host "if (element) {"
Write-Host "  element.scrollIntoView({ behavior: 'smooth', block: 'center' });"
Write-Host "  element.style.outline = '3px solid red';"
Write-Host "  console.log('Element found and highlighted!');"
Write-Host "  console.log('Element dimensions:', element.offsetWidth, 'x', element.offsetHeight);"
Write-Host "} else {"
Write-Host "  console.error('Element not found!');"
Write-Host "}"
Write-Host ""
Write-Host "5. Use DevTools > ... > Capture node screenshot (right-click the highlighted element)"

# Open browser
Start-Process msedge $url

Write-Host "`nAlternatively, use Chrome/Edge screenshot feature:"
Write-Host "1. Open DevTools (F12)"
Write-Host "2. Open Command Menu (Ctrl+Shift+P)"
Write-Host "3. Type 'screenshot'"
Write-Host "4. Select 'Capture node screenshot'"
Write-Host "5. Click on the injury risk card element in the inspector"
