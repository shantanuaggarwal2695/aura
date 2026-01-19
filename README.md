# Conversational AI Webapp

A Python web application that provides a conversational interface using both voice and text input. The app integrates with Hume.ai for speech-to-text conversion and Google ADK (Agentic AI) for generating intelligent responses.

## Features

- **Dual Input Modes**: Users can interact via voice or text
- **Voice Recording**: Real-time voice input with visual feedback
- **Speech-to-Text**: Powered by Hume.ai API
- **AI Responses**: Powered by Google ADK (Gemini) for intelligent conversations
- **Chat Interface**: Modern, responsive UI with conversation history
- **Session Management**: Tracks conversations across sessions
- **Error Handling**: Robust error handling and user feedback
- **Logging**: Comprehensive logging for debugging and analytics

## Project Structure

```
aura/
├── app.py                      # Main FastAPI application
├── requirements.txt            # Python dependencies
├── environment.yml             # Conda environment file
├── config.example.env           # Environment variables template
├── README.md                   # This file
├── integrations/
│   ├── __init__.py
│   ├── hume_client.py         # Hume.ai API client
│   └── google_adk_client.py   # Google ADK API client
├── services/
│   ├── __init__.py
│   └── conversation_service.py # Conversation history management
└── static/
    ├── index.html             # Frontend HTML
    ├── styles.css             # Frontend styles
    └── app.js                 # Frontend JavaScript
```

## Setup Instructions

### 1. Set Up Python Environment

Choose one of the following methods:

#### Option A: Using Conda (Recommended)

**Quick Setup (using environment.yml):**
```bash
conda env create -f environment.yml
conda activate aura
```

**Manual Setup:**
1. **Create a new conda environment:**
   ```bash
   conda create -n aura python=3.11
   conda activate aura
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   Or install via conda if packages are available:
   ```bash
   conda install -c conda-forge fastapi uvicorn httpx python-dotenv
   pip install -r requirements.txt  # Install remaining packages via pip
   ```

3. **Deactivate environment when done:**
   ```bash
   conda deactivate
   ```

**Note:** To remove the conda environment later:
```bash
conda deactivate
conda env remove -n aura
```

#### Option B: Using Python venv

1. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Deactivate environment when done:**
   ```bash
   deactivate
   ```

### 2. Configure Environment Variables

Copy `config.example.env` to `.env` and fill in your API keys:

```bash
cp config.example.env .env
```

Edit `.env` with your credentials:

```env
HUME_API_KEY=your_hume_api_key_here
GOOGLE_ADK_API_KEY=your_google_adk_api_key_here
DEBUG=True
LOG_LEVEL=INFO
```

### 3. Activate Your Environment

**If using Conda:**
```bash
conda activate aura
```

**If using venv:**
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Get API Keys

- **Hume.ai**: Sign up at [https://www.hume.ai/](https://www.hume.ai/) and get your API key
- **Google ADK**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey) or Google Cloud Console

### 5. Run the Application

```bash
python app.py
```

Or using uvicorn directly:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Access the Webapp

Open your browser and navigate to:
```
http://localhost:8000
```

## Usage

### Text Input
1. Type your message in the text input field
2. Press Enter or click the Send button
3. The AI response will appear in the chat

### Voice Input
1. Click the microphone button to start recording
2. Speak your message
3. Click the microphone button again to stop recording
4. The audio will be transcribed and sent to the AI
5. The AI response will appear in the chat

## API Endpoints

### POST `/api/chat`
Send a text message and receive an AI response.

**Request:**
```json
{
  "message": "Hello, how are you?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "response": "I'm doing well, thank you!",
  "session_id": "session-uuid",
  "timestamp": "2024-01-01T12:00:00"
}
```

### POST `/api/voice/transcribe`
Transcribe audio file to text.

**Request:** Multipart form data with `audio` file

**Response:**
```json
{
  "transcription": "Hello, this is my voice message",
  "status": "success"
}
```

### POST `/api/voice/synthesize`
Synthesize text to speech (optional).

**Request:**
```json
{
  "text": "Hello, this is a test"
}
```

### GET `/api/conversations/{session_id}`
Get conversation history for a session.

### GET `/api/health`
Health check endpoint.

## Configuration Notes

### Hume.ai Integration
The Hume.ai client in `integrations/hume_client.py` uses placeholder endpoints. You'll need to:
1. Check the [Hume.ai API documentation](https://dev.hume.ai/docs) for actual endpoints
2. Update the endpoint URLs in `hume_client.py`
3. Adjust the response parsing based on the actual API response structure

### Google ADK Integration
The Google ADK client uses the Gemini API. You may need to:
1. Adjust the model name (`gemini-pro` or `gemini-pro-vision`)
2. Update the API endpoint if using a different Google ADK service
3. Modify generation parameters (temperature, max tokens, etc.) as needed

## Development

### Adding Features
- **Database Storage**: Replace in-memory storage in `conversation_service.py` with a database (SQLite, PostgreSQL, etc.)
- **WebSocket Support**: Add WebSocket endpoints for real-time streaming responses
- **Authentication**: Add user authentication and session management
- **TTS Integration**: Implement text-to-speech for AI responses

### Error Handling
The application includes error handling at multiple levels:
- API client errors are caught and logged
- HTTP exceptions are returned with appropriate status codes
- Frontend displays user-friendly error messages

### Logging
Logs are configured in `app.py` and can be adjusted via the `LOG_LEVEL` environment variable. Logs include:
- API requests and responses
- Error details with stack traces
- Session creation and message handling

## Troubleshooting

### Microphone Not Working
- Check browser permissions for microphone access
- Ensure you're using HTTPS (required for microphone access in most browsers)
- Try a different browser (Chrome, Firefox, Safari)

### API Errors
- Verify your API keys are correct in `.env`
- Check API rate limits and quotas
- Review logs for detailed error messages

### Conda Environment Issues
- If conda command is not found, install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/products/distribution)
- To update conda: `conda update conda`
- To list all environments: `conda env list`
- If environment creation fails, try: `conda clean --all` then recreate

### CORS Issues
- Adjust CORS settings in `app.py` for production
- Ensure frontend and backend are on the same domain or configure allowed origins

## License

This project is provided as-is for educational and development purposes.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.
