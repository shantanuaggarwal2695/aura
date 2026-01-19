# Environment Variables Reference

Complete list of all environment variables used by the Aura application.

## Required Variables (Must Set)

These variables are **required** for the application to function:

| Variable Name | Description | Example Value |
|--------------|-------------|---------------|
| `HUME_API_KEY` | Your Hume.ai API key for speech-to-text | `MeRAKQjlPi5ggUJpUsOvjdR9qLrYh26Zku5q7rW0mqU9ikgZ` |
| `GOOGLE_ADK_API_KEY` | Your Google Gemini API key for AI responses | `AIzaSyCCq1lpXJ0MI8xU2EEM9Sz86ACvYKIO4Wg` |

**Note:** Without these, the app will start but voice transcription and AI responses won't work.

---

## Optional Variables (Recommended)

These variables have defaults but can be customized:

| Variable Name | Default Value | Description | Example |
|--------------|---------------|-------------|---------|
| `GOOGLE_ADK_MODEL_NAME` | `gemini-2.5-flash-lite` | Gemini model to use | `gemini-2.5-flash-lite`, `gemini-1.5-pro`, `gemini-2.5-flash` |
| `GOOGLE_ADK_API_URL` | `https://generativelanguage.googleapis.com/v1beta` | Google API endpoint | (usually keep default) |
| `GOOGLE_ADK_SYSTEM_INSTRUCTION` | `None` | System prompt for the AI | `You are a helpful, friendly assistant.` |
| `HUME_API_URL` | `https://api.hume.ai` | Hume.ai API endpoint | (usually keep default) |
| `LLM_PROVIDER` | `gemini` | LLM provider type | `gemini`, `openai_compatible`, `huggingface` |
| `LLM_API_KEY` | (inherits from `GOOGLE_ADK_API_KEY`) | Unified LLM API key | (use if not using `GOOGLE_ADK_API_KEY`) |
| `LLM_API_URL` | (inherits from `GOOGLE_ADK_API_URL`) | Unified LLM API URL | (use if not using `GOOGLE_ADK_API_URL`) |
| `LLM_MODEL_NAME` | (inherits from `GOOGLE_ADK_MODEL_NAME`) | Unified LLM model name | (use if not using `GOOGLE_ADK_MODEL_NAME`) |
| `LLM_SYSTEM_INSTRUCTION` | (inherits from `GOOGLE_ADK_SYSTEM_INSTRUCTION`) | Unified system instruction | (use if not using `GOOGLE_ADK_SYSTEM_INSTRUCTION`) |

---

## System Variables (Railway Sets Automatically)

These are set automatically by Railway - **do not set manually:**

| Variable Name | Description | Set By |
|--------------|-------------|--------|
| `PORT` | Port number for the application | Railway (automatically) |
| `RAILWAY_ENVIRONMENT` | Deployment environment | Railway |
| `RAILWAY_PROJECT_ID` | Project identifier | Railway |

---

## Configuration Variables

| Variable Name | Default Value | Description | Recommended Value |
|--------------|---------------|-------------|-------------------|
| `DEBUG` | `False` | Enable debug mode | `False` for production |
| `LOG_LEVEL` | `INFO` | Logging level | `INFO` or `DEBUG` |
| `ALLOWED_ORIGINS` | `*` | CORS allowed origins | Your domain in production (e.g., `https://yourdomain.com`) |

---

## Minimum Railway Setup (Required Only)

For Railway deployment, **minimum required variables:**

```
HUME_API_KEY=your_hume_api_key_here
GOOGLE_ADK_API_KEY=your_google_api_key_here
```

---

## Recommended Railway Setup

For Railway deployment, **recommended variables:**

```
# Required
HUME_API_KEY=your_hume_api_key_here
GOOGLE_ADK_API_KEY=your_google_api_key_here

# Recommended
GOOGLE_ADK_MODEL_NAME=gemini-2.5-flash-lite
DEBUG=False
LOG_LEVEL=INFO
```

---

## Production Setup (Full Configuration)

For production deployment with custom configuration:

```
# Required
HUME_API_KEY=your_hume_api_key_here
GOOGLE_ADK_API_KEY=your_google_api_key_here

# LLM Configuration
GOOGLE_ADK_MODEL_NAME=gemini-2.5-flash-lite
GOOGLE_ADK_SYSTEM_INSTRUCTION=You are a helpful, friendly, and knowledgeable AI assistant. You provide clear, concise, and accurate responses to user questions. Be conversational and engaging while maintaining professionalism.

# Application Configuration
DEBUG=False
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

## Variable Priority (How Variables Are Loaded)

1. **New Unified Variables** (highest priority):
   - `LLM_API_KEY`, `LLM_MODEL_NAME`, `LLM_SYSTEM_INSTRUCTION`

2. **Legacy Variables** (backward compatibility):
   - `GOOGLE_ADK_API_KEY`, `GOOGLE_ADK_MODEL_NAME`, `GOOGLE_ADK_SYSTEM_INSTRUCTION`

3. **Defaults** (if nothing is set):
   - Model: `gemini-2.5-flash-lite`
   - Provider: `gemini`

---

## Quick Copy-Paste for Railway

### Minimal Setup (Required Only):
```
HUME_API_KEY=your_hume_api_key
GOOGLE_ADK_API_KEY=your_google_api_key
```

### Recommended Setup:
```
HUME_API_KEY=your_hume_api_key
GOOGLE_ADK_API_KEY=your_google_api_key
GOOGLE_ADK_MODEL_NAME=gemini-2.5-flash-lite
ADMIN_KEY=your_secure_admin_key_here
DEBUG=False
LOG_LEVEL=INFO
```

---

## How to Verify Variables Are Set

After deploying, check the logs for:
- `✅ Successfully loaded .env file` or `⚠️ No .env file found. Using system environment variables only.`
- `Hume.ai API Key: AIza...xyz1 (length: 39)` ← Should show masked key
- `LLM API Key: AIza...abc2 (length: 39)` ← Should show masked key
- `LLM Model: gemini-2.5-flash-lite` ← Should show your model

If you see `NOT_SET`, the variable is missing from Railway dashboard.
