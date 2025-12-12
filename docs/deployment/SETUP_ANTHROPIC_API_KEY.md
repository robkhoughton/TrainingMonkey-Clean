# Setting Up Anthropic API Key for Screenshot Parsing

The Race History screenshot upload feature uses Claude Vision API to extract race data from ultrasignup.com screenshots.

## Step 1: Get Your Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to "API Keys"
4. Create a new API key
5. Copy the key (it starts with `sk-ant-api03-...`)

## Step 2: Add to Cloud Run Environment

### Option A: Using Google Cloud Console (Easiest)

1. Go to https://console.cloud.google.com/run
2. Select your project: `dev-ruler-460822-e8`
3. Click on your service: `strava-training-personal`
4. Click "EDIT & DEPLOY NEW REVISION"
5. Click "VARIABLES & SECRETS" tab
6. Under "Environment variables", click "+ ADD VARIABLE"
7. Set:
   - Name: `ANTHROPIC_API_KEY`
   - Value: `your-api-key-here` (paste your actual key)
8. Click "DEPLOY"

### Option B: Using gcloud CLI

```bash
gcloud run services update strava-training-personal \
  --region=us-central1 \
  --update-env-vars ANTHROPIC_API_KEY=your-api-key-here
```

## Step 3: Verify

1. Go to your Coach page
2. Click "Upload Screenshot" under Race History
3. Select a screenshot from ultrasignup.com
4. Click "Upload & Parse"
5. You should see extracted race data (no more "not configured" error)

## Cost Estimates

- Claude 3.5 Sonnet: ~$3 per 1M input tokens, ~$15 per 1M output tokens
- Typical screenshot parsing: ~2,000 input tokens (image) + 500 output tokens
- **Cost per screenshot: ~$0.01 - $0.02**
- Very affordable for occasional use!

## Notes

- The API key is stored as an environment variable (secure)
- It's never exposed to the frontend
- Only the backend uses it to call Claude Vision API
- The feature works without the key (just shows the error message)




