Write-Host "Starting TrainingMonkey deployment process..." -ForegroundColor Green

Write-Host ""
Write-Host "Step 1: Rebuilding React App..." -ForegroundColor Yellow

# Navigate to frontend directory
Set-Location "C:\Users\robho\Documents\TrainingMonkey-Clean\frontend"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to navigate to frontend directory" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host "Cleaning previous build..."
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}

Write-Host "Installing dependencies..."
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: npm install failed" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host "Building React app (this may take a few minutes)..."
$env:CI = "false"
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: npm run build failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common solutions:"
    Write-Host "1. Check for TypeScript errors in the console above"
    Write-Host "2. Ensure all dependencies are installed"
    Write-Host "3. Try running 'npm run build' manually in the frontend directory"
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host ""
Write-Host "Step 2: Copying build files to app directory..." -ForegroundColor Yellow

# Navigate to project root
Set-Location "C:\Users\robho\Documents\TrainingMonkey-Clean"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to navigate to project root" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host "Creating app\build directory if it doesn't exist..."
if (-not (Test-Path "app\build")) {
    New-Item -ItemType Directory -Path "app\build" -Force
}

Write-Host "Copying build files..."
robocopy frontend\build app\build /E /NFL /NDL /NJH /NJS /nc /ns /np
if ($LASTEXITCODE -gt 7) {
    Write-Host "Error: Failed to copy build files" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}
Write-Host "Build files copied successfully." -ForegroundColor Green

Write-Host "Copying static files for local development..."
robocopy frontend\build\static app\static /E /NFL /NDL /NJH /NJS /nc /ns /np
if ($LASTEXITCODE -gt 7) {
    Write-Host "Error: Failed to copy static files" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}
Write-Host "Static files copied successfully." -ForegroundColor Green

Write-Host ""
Write-Host "Step 3: Deploying to Cloud Run..." -ForegroundColor Yellow

# Navigate to app directory
Set-Location "C:\Users\robho\Documents\TrainingMonkey-Clean\app"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to navigate to app directory" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

# Run the deployment script
& ".\deploy_strava_simple.bat"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Deployment failed" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host ""
Write-Host "Deployment completed successfully!" -ForegroundColor Green
Read-Host "Press Enter to continue"
