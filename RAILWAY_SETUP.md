# Railway Deployment - Environment Variables Setup

## ⚠️ IMPORTANT: Environment Variables Required

Railway **does NOT use** a `.env` file from GitHub. You must set environment variables in the Railway dashboard.

## Step-by-Step: Setting Environment Variables in Railway

1. **Go to your Railway project dashboard**
   - Visit [railway.app](https://railway.app)
   - Click on your project
   - Click on the service (your deployed app)

2. **Open Variables tab**
   - Click on "Variables" tab (or go to Settings → Variables)
   - This is where you add environment variables

3. **Add Required Variables**

   Click "New Variable" for each of these:

   ### Required Variables (MUST SET):
   
   | Variable Name | Value | Description |
   |--------------|-------|-------------|
   | `HUME_API_KEY` | `your_hume_api_key_here` | Your Hume.ai API key for voice transcription |
   | `GOOGLE_ADK_API_KEY` | `your_google_api_key_here` | Your Google Gemini API key for AI responses |
   
   **Without these, the app will start but won't work properly!**
   
   ### Recommended Variables (Optional but Recommended):
   
   | Variable Name | Value | Description |
   |--------------|-------|-------------|
   | `GOOGLE_ADK_MODEL_NAME` | `gemini-2.5-flash-lite` | Gemini model to use (default: gemini-2.5-flash-lite) |
   | `GOOGLE_ADK_SYSTEM_INSTRUCTION` | `You are a helpful...` | System prompt for AI behavior |
   | `DEBUG` | `False` | Debug mode (use False in production) |
   | `LOG_LEVEL` | `INFO` | Logging level (INFO or DEBUG) |
   
   ### Optional Variables (Advanced):
   
   | Variable Name | Value | Description |
   |--------------|-------|-------------|
   | `LLM_PROVIDER` | `gemini` | LLM provider (default: gemini, can be openai_compatible or huggingface) |
   | `HUME_API_URL` | `https://api.hume.ai` | Hume.ai API URL (usually keep default) |
   | `GOOGLE_ADK_API_URL` | `https://generativelanguage.googleapis.com/v1beta` | Google API URL (usually keep default) |
   | `ALLOWED_ORIGINS` | `*` | CORS allowed origins (set to your domain in production) |
   
   **See `ENVIRONMENT_VARIABLES.md` for complete variable reference.**

4. **Save and Redeploy**
   - After adding all variables, Railway will automatically redeploy
   - Or manually trigger a redeploy if needed

5. **Verify Deployment**
   - Check the deployment logs to ensure variables are loaded
   - Look for logs showing:
     ```
     ✅ Successfully loaded .env file (or using system environment variables)
     Hume.ai API Key: AIza...xyz1 (length: 39)
     LLM API Key: AIza...abc2 (length: 39)
     ```

## How to Get API Keys

### Hume.ai API Key:
1. Sign up at [https://www.hume.ai/](https://www.hume.ai/)
2. Go to API Keys section in your dashboard
3. Generate a new API key
4. Copy the key and add it to Railway as `HUME_API_KEY`

### Google Gemini API Key:
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key and add it to Railway as `GOOGLE_ADK_API_KEY`

## Troubleshooting

### "API key is not configured" error:
- ✅ Check that variables are set in Railway dashboard (Variables tab)
- ✅ Verify variable names match exactly: `GOOGLE_ADK_API_KEY` (case-sensitive)
- ✅ Make sure there are no extra spaces in the variable names or values
- ✅ Trigger a new deployment after adding variables

### Variables not being read:
- Railway may cache environment variables. Try:
  1. Save all variables again
  2. Trigger a manual redeploy
  3. Check deployment logs for variable loading

### How to manually redeploy:
- Go to Deployments tab
- Click "Redeploy" on the latest deployment
- Or push a new commit to trigger deployment

## Security Notes

- ✅ Never commit your `.env` file to GitHub
- ✅ Use Railway's Variables tab for sensitive keys
- ✅ Railway encrypts environment variables at rest
- ✅ Each Railway project has isolated environment variables
