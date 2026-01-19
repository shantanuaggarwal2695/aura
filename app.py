"""
Main FastAPI application for conversational AI webapp.
Supports both voice and text input with Hume.ai STT and Google ADK AI responses.
"""

import os
import logging
import pathlib
import hashlib
import csv
import io
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from integrations.hume_client import HumeClient
from integrations.llm_client import LLMClient
from services.conversation_service import ConversationService

# Configure logging first (before loading .env so we can log about it)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
env_loaded = load_dotenv()
if env_loaded:
    logger.info("✅ Successfully loaded .env file")
    # Try to get the .env file path for logging
    env_file = pathlib.Path(".env")
    if env_file.exists():
        logger.info(f"   .env file location: {env_file.absolute()}")
else:
    logger.warning("⚠️ No .env file found. Using system environment variables only.")
    logger.warning("   Please create a .env file in the project root with your API keys.")
    logger.warning(f"   Expected location: {pathlib.Path('.').absolute()}/.env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources on app startup/shutdown."""
    # Initialize clients
    logger.info("Initializing application...")
    
    # Helper function to mask API keys for logging
    def mask_api_key(key: Optional[str], show_length: bool = True) -> str:
        """Mask API key for safe logging."""
        if not key or key in ["your_hume_api_key_here", "your_google_adk_api_key_here", "your_huggingface_token_here"]:
            return "NOT_SET"
        if len(key) <= 8:
            return "***"  # Too short to mask safely
        masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "***"
        if show_length:
            return f"{masked} (length: {len(key)})"
        return masked
    
    # Validate and log API keys
    hume_api_key = os.getenv("HUME_API_KEY")
    logger.info(f"Hume.ai API Key: {mask_api_key(hume_api_key)}")
    
    if not hume_api_key or hume_api_key == "your_hume_api_key_here":
        logger.warning("HUME_API_KEY not set or using placeholder. Voice transcription may not work.")
    
    app.state.hume_client = HumeClient(
        api_key=hume_api_key or "",
        api_url=os.getenv("HUME_API_URL", "https://api.hume.ai")
    )
    logger.info(f"Hume.ai API URL: {os.getenv('HUME_API_URL', 'https://api.hume.ai')}")
    
    # Initialize LLM client (supports Gemini, OpenAI-compatible, and Hugging Face)
    llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    llm_api_key = os.getenv("LLM_API_KEY", "")
    llm_api_url = os.getenv("LLM_API_URL")
    # Default to gemini-2.5-flash-lite (latest efficient model)
    llm_model_name = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash-lite")
    llm_system_instruction = os.getenv("LLM_SYSTEM_INSTRUCTION")
    
    # Debug: Log what we found in environment
    logger.debug(f"Environment check - LLM_API_KEY: {'SET' if llm_api_key else 'NOT_SET'}")
    logger.debug(f"Environment check - GOOGLE_ADK_API_KEY: {'SET' if os.getenv('GOOGLE_ADK_API_KEY') else 'NOT_SET'}")
    
    # Backward compatibility: use old env vars if new ones not set
    if llm_provider == "gemini" and not llm_api_key:
        google_adk_key = os.getenv("GOOGLE_ADK_API_KEY", "")
        logger.debug(f"Falling back to GOOGLE_ADK_API_KEY: {'SET' if google_adk_key else 'NOT_SET'}")
        if google_adk_key:
            llm_api_key = google_adk_key
        if not llm_api_url:
            llm_api_url = os.getenv("GOOGLE_ADK_API_URL", "https://generativelanguage.googleapis.com/v1beta")
        # Use GOOGLE_ADK_MODEL_NAME if set, otherwise keep default
        google_model = os.getenv("GOOGLE_ADK_MODEL_NAME")
        if google_model:
            llm_model_name = google_model
        elif llm_model_name == "gemini-pro":
            # Default to gemini-2.5-flash-lite as gemini-pro is deprecated
            llm_model_name = "gemini-2.5-flash-lite"
        if not llm_system_instruction:
            llm_system_instruction = os.getenv("GOOGLE_ADK_SYSTEM_INSTRUCTION")
    
    # Log LLM configuration
    logger.info(f"LLM Provider: {llm_provider}")
    logger.info(f"LLM API Key: {mask_api_key(llm_api_key)}")
    logger.info(f"LLM API URL: {llm_api_url or 'default'}")
    logger.info(f"LLM Model: {llm_model_name}")
    logger.info(f"LLM System Instruction: {'SET' if llm_system_instruction else 'NOT_SET'}")
    
    # Additional validation logging
    if llm_provider == "gemini":
        if not llm_api_key or llm_api_key in ["your_google_adk_api_key_here", "your_hume_api_key_here"]:
            logger.warning("⚠️ Gemini API key is missing or using placeholder value!")
            logger.warning("   Please check your .env file and ensure GOOGLE_ADK_API_KEY is set correctly.")
            logger.warning("   Make sure the .env file is in the project root directory.")
        else:
            logger.info("✅ Gemini API key is configured")
        
        # Warn if using deprecated or potentially unavailable models
        deprecated_models = ["gemini-pro", "gemini-1.5-flash"]
        if llm_model_name in deprecated_models:
            logger.warning(f"⚠️ Model '{llm_model_name}' may not be available in v1beta API.")
            logger.warning(f"   Consider updating to 'gemini-2.5-flash-lite' in your .env file:")
            logger.warning(f"   GOOGLE_ADK_MODEL_NAME=gemini-2.5-flash-lite")
    
    if llm_provider == "gemini" and (not llm_api_key or llm_api_key == "your_google_adk_api_key_here"):
        logger.warning("LLM_API_KEY (or GOOGLE_ADK_API_KEY) not set. AI responses may not work.")
    elif llm_provider in ["openai_compatible", "huggingface"] and not llm_api_key:
        logger.info(f"Using {llm_provider} provider without API key (may work for local models)")
    
    app.state.llm_client = LLMClient(
        provider=llm_provider,
        api_key=llm_api_key or None,
        api_url=llm_api_url,
        model_name=llm_model_name,
        system_instruction=llm_system_instruction
    )
    
    # Backward compatibility alias
    app.state.google_adk_client = app.state.llm_client
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
# In production, update allow_origins to only include your domain
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if "*" not in allowed_origins else ["*"],
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
        
        # Get AI response from LLM (supports Gemini, OpenAI-compatible, Hugging Face)
        ai_response = await app.state.llm_client.get_response(
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


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    """Serve the admin panel page."""
    try:
        with open("static/admin.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Error: Admin panel not found. Please ensure static/admin.html exists.</h1>",
            status_code=404
        )


def verify_admin_key(admin_key: Optional[str] = None) -> bool:
    """
    Verify admin access key.
    
    Args:
        admin_key: Admin key from request
        
    Returns:
        True if admin key is valid
    """
    expected_key = os.getenv("ADMIN_KEY", "")
    if not expected_key:
        # If no ADMIN_KEY is set, allow access (for development)
        # In production, always set ADMIN_KEY
        logger.warning("ADMIN_KEY not set - allowing admin access (NOT SECURE FOR PRODUCTION)")
        return True
    
    if not admin_key:
        return False
    
    # Simple comparison (in production, use secure comparison)
    return admin_key == expected_key


@app.get("/api/admin/stats")
async def get_admin_stats(admin_key: Optional[str] = None):
    """
    Get statistics about all conversations.
    
    Args:
        admin_key: Admin authentication key (query parameter)
        
    Returns:
        Statistics about conversations
    """
    if not verify_admin_key(admin_key):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin key")
    
    try:
        all_sessions = app.state.conversation_service.get_all_sessions()
        total_sessions = len(all_sessions)
        total_messages = sum(len(messages) for messages in all_sessions.values())
        
        # Count messages by role
        user_messages = 0
        assistant_messages = 0
        for messages in all_sessions.values():
            for msg in messages:
                role = msg.get("role", "")
                if role == "user":
                    user_messages += 1
                elif role == "assistant":
                    assistant_messages += 1
        
        return JSONResponse(content={
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting admin stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@app.get("/api/admin/conversations")
async def get_all_conversations(admin_key: Optional[str] = None):
    """
    Get all conversations (anonymous format).
    
    Args:
        admin_key: Admin authentication key (query parameter)
        
    Returns:
        List of all conversations with anonymized session IDs
    """
    if not verify_admin_key(admin_key):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin key")
    
    try:
        conversations = app.state.conversation_service.get_all_conversations_anonymous()
        return JSONResponse(content={
            "conversations": conversations,
            "total_conversations": len(conversations),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting conversations: {str(e)}")


@app.get("/api/admin/download/csv")
async def download_conversations_csv(admin_key: Optional[str] = None):
    """
    Download all conversations as CSV (anonymous format).
    
    Args:
        admin_key: Admin authentication key (query parameter)
        
    Returns:
        CSV file with all conversations
    """
    if not verify_admin_key(admin_key):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin key")
    
    try:
        conversations = app.state.conversation_service.get_all_conversations_anonymous()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Session ID (Anonymized)", "Message Number", "Role", "Content", "Timestamp"])
        
        # Write conversations
        for conv in conversations:
            session_id_hash = conv["session_id_hash"]
            for idx, msg in enumerate(conv["messages"], 1):
                writer.writerow([
                    session_id_hash,
                    idx,
                    msg["role"],
                    msg["content"],
                    msg["timestamp"]
                ])
        
        # Convert to bytes
        csv_content = output.getvalue().encode('utf-8')
        output.close()
        
        # Create filename with timestamp
        filename = f"aura_conversations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        from fastapi.responses import Response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Error generating CSV: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating CSV: {str(e)}")


@app.get("/api/admin/download/json")
async def download_conversations_json(admin_key: Optional[str] = None):
    """
    Download all conversations as JSON (anonymous format).
    
    Args:
        admin_key: Admin authentication key (query parameter)
        
    Returns:
        JSON file with all conversations
    """
    if not verify_admin_key(admin_key):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin key")
    
    try:
        conversations = app.state.conversation_service.get_all_conversations_anonymous()
        
        json_data = {
            "exported_at": datetime.now().isoformat(),
            "total_conversations": len(conversations),
            "conversations": conversations
        }
        
        import json as json_lib
        json_content = json_lib.dumps(json_data, indent=2, ensure_ascii=False).encode('utf-8')
        
        # Create filename with timestamp
        filename = f"aura_conversations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        from fastapi.responses import Response
        return Response(
            content=json_content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Error generating JSON: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating JSON: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=debug
    )
