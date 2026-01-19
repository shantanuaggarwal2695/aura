"""
Main FastAPI application for conversational AI webapp.
Supports both voice and text input with Hume.ai STT and Google ADK AI responses.
"""

import os
import logging
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from integrations.hume_client import HumeClient
from integrations.google_adk_client import GoogleADKClient
from services.conversation_service import ConversationService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources on app startup/shutdown."""
    # Initialize clients
    logger.info("Initializing application...")
    
    # Validate API keys
    hume_api_key = os.getenv("HUME_API_KEY")
    google_adk_api_key = os.getenv("GOOGLE_ADK_API_KEY")
    
    if not hume_api_key or hume_api_key == "your_hume_api_key_here":
        logger.warning("HUME_API_KEY not set or using placeholder. Voice transcription may not work.")
    
    if not google_adk_api_key or google_adk_api_key == "your_google_adk_api_key_here":
        logger.warning("GOOGLE_ADK_API_KEY not set or using placeholder. AI responses may not work.")
    
    app.state.hume_client = HumeClient(
        api_key=hume_api_key or "",
        api_url=os.getenv("HUME_API_URL", "https://api.hume.ai")
    )
    app.state.google_adk_client = GoogleADKClient(
        api_key=google_adk_api_key or "",
        api_url=os.getenv("GOOGLE_ADK_API_URL", "https://generativelanguage.googleapis.com/v1beta")
    )
    app.state.conversation_service = ConversationService()
    logger.info("Application initialized successfully")
    yield
    # Cleanup (if needed)
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="Conversational AI Webapp",
    description="Voice and text conversational interface with Hume.ai and Google ADK",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (for serving HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")


# Pydantic models for request/response
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page."""
    try:
        with open("static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Error: Frontend not found. Please ensure static/index.html exists.</h1>",
            status_code=404
        )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Process text message and return AI response.
    
    Args:
        message: ChatMessage containing user text and optional session_id
        
    Returns:
        ChatResponse with AI response, session_id, and timestamp
    """
    try:
        logger.info(f"Received chat message: {message.message[:50]}...")
        
        # Get session ID or create new one
        session_id = message.session_id or app.state.conversation_service.create_session()
        
        # Store user message in conversation service
        app.state.conversation_service.add_message(session_id, "user", message.message)
        
        # Get AI response from Google ADK
        ai_response = await app.state.google_adk_client.get_response(
            message=message.message,
            conversation_history=app.state.conversation_service.get_session_history(session_id)
        )
        
        # Store AI response in conversation service
        app.state.conversation_service.add_message(session_id, "assistant", ai_response)
        
        logger.info(f"Generated AI response: {ai_response[:50]}...")
        
        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@app.post("/api/voice/transcribe")
async def transcribe_voice(audio: UploadFile = File(...)):
    """
    Transcribe audio file using Hume.ai speech-to-text.
    
    Args:
        audio: Audio file (WAV, MP3, etc.)
        
    Returns:
        JSON with transcribed text
    """
    try:
        logger.info(f"Received audio file: {audio.filename}, content_type: {audio.content_type}")
        
        # Read audio file
        audio_data = await audio.read()
        
        # Transcribe using Hume.ai
        transcription = await app.state.hume_client.transcribe_audio(audio_data)
        
        logger.info(f"Transcription: {transcription}")
        
        return JSONResponse(content={
            "transcription": transcription,
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")


@app.post("/api/voice/synthesize")
async def synthesize_voice(request: dict):
    """
    Synthesize text to speech using Hume.ai (optional TTS).
    
    Args:
        request: Dict with 'text' key containing text to synthesize
        
    Returns:
        Audio file or URL to audio
    """
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        logger.info(f"Synthesizing text: {text[:50]}...")
        
        # Synthesize using Hume.ai (if TTS is available)
        audio_url = await app.state.hume_client.synthesize_text(text)
        
        return JSONResponse(content={
            "audio_url": audio_url,
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error synthesizing text: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error synthesizing text: {str(e)}")


@app.get("/api/conversations/{session_id}")
async def get_conversation_history(session_id: str):
    """
    Get conversation history for a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        List of messages in the conversation
    """
    try:
        history = app.state.conversation_service.get_session_history(session_id)
        return JSONResponse(content={
            "session_id": session_id,
            "messages": history,
            "total_messages": len(history)
        })
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )
