# PowerShell script to set up Cloud Scheduler job for proactive token refresh

Write-Host "Setting up Cloud Scheduler job for proactive token refresh..." -ForegroundColor Green

try {
    # Create the Cloud Scheduler job for token refresh
    # This runs daily at 5 AM UTC (before the 6 AM sync job)
    $jobName = "daily-token-refresh"
    $schedule = "0 5 * * *"
    $uri = "https://strava-training-personal-382535371225.us-central1.run.app/cron/token-refresh"
    $location = "us-central1"
    
    Write-Host "Creating Cloud Scheduler job: $jobName" -ForegroundColor Yellow
    Write-Host "Schedule: $schedule (Daily at 5:00 AM UTC)" -ForegroundColor Yellow
    Write-Host "Endpoint: $uri" -ForegroundColor Yellow
    
    gcloud scheduler jobs create http $jobName `
        --schedule=$schedule `
        --uri=$uri `
        --http-method=POST `
        --headers="Content-Type=application/json,X-Cloudscheduler=true" `
        --location=$location `
        --description="Daily proactive token refresh for all users"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Token refresh scheduler job created successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Job Details:" -ForegroundColor Cyan
        Write-Host "- Schedule: Daily at 5:00 AM UTC" -ForegroundColor White
        Write-Host "- Endpoint: /cron/token-refresh" -ForegroundColor White
        Write-Host "- Purpose: Proactively refresh Strava tokens before they expire" -ForegroundColor White
        Write-Host ""
        Write-Host "This will run 1 hour before the daily sync job to ensure tokens are fresh." -ForegroundColor Yellow
    } else {
        Write-Host "❌ Failed to create token refresh scheduler job" -ForegroundColor Red
        Write-Host "Error code: $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error creating scheduler job: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "To verify the job was created, run:" -ForegroundColor Cyan
Write-Host "gcloud scheduler jobs list --location=$location" -ForegroundColor White
Write-Host ""
Write-Host "To test the job manually, run:" -ForegroundColor Cyan
Write-Host "gcloud scheduler jobs run $jobName --location=$location" -ForegroundColor White
