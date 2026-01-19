"""
Hume.ai client for speech-to-text and text-to-speech conversion.
"""

import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)


class HumeClient:
    """Client for interacting with Hume.ai API for voice processing."""
    
    def __init__(self, api_key: str, api_url: str = "https://api.hume.ai"):
        """
        Initialize Hume.ai client.
        
        Args:
            api_key: Hume.ai API key
            api_url: Base URL for Hume.ai API
        """
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.headers = {
            "X-Hume-Api-Key": api_key,
            "Content-Type": "application/json"
        }
        
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe audio to text using Hume.ai speech-to-text.
        
        Args:
            audio_data: Raw audio bytes (WAV, MP3, etc.)
            
        Returns:
            Transcribed text string
            
        Note:
            This is a placeholder implementation. Actual Hume.ai API endpoints
            may vary. You'll need to check Hume.ai documentation for the exact
            endpoint and request format.
        """
        try:
            # Note: Hume.ai API structure may vary. This is a template.
            # Check https://dev.hume.ai/docs for actual API endpoints
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Example endpoint - adjust based on actual Hume.ai API
                url = f"{self.api_url}/v0/evi/transcriptions"
                
                # Prepare multipart form data
                files = {
                    "audio": ("audio.wav", audio_data, "audio/wav")
                }
                
                headers = {
                    "X-Hume-Api-Key": self.api_key
                }
                
                response = await client.post(
                    url,
                    files=files,
                    headers=headers
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Extract transcription from response
                # Adjust based on actual Hume.ai response structure
                transcription = result.get("transcription", "") or result.get("text", "")
                
                if not transcription:
                    logger.warning("Empty transcription received from Hume.ai")
                    raise ValueError("Empty transcription received")
                
                logger.info(f"Successfully transcribed audio: {transcription[:50]}...")
                return transcription
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Hume.ai API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Hume.ai API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error transcribing audio with Hume.ai: {str(e)}", exc_info=True)
            raise
    
    async def synthesize_text(self, text: str) -> Optional[str]:
        """
        Synthesize text to speech using Hume.ai (optional TTS).
        
        Args:
            text: Text to convert to speech
            
        Returns:
            URL or path to generated audio file
            
        Note:
            This is a placeholder implementation. Hume.ai may or may not
            support TTS. Adjust based on actual API capabilities.
        """
        try:
            # Note: Check if Hume.ai supports TTS in their API
            # This is a placeholder implementation
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.api_url}/v0/evi/synthesize"  # Adjust endpoint as needed
                
                payload = {
                    "text": text,
                    "voice": "default"  # Adjust based on available voices
                }
                
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Extract audio URL or data
                audio_url = result.get("audio_url") or result.get("url")
                
                logger.info(f"Successfully synthesized text to speech")
                return audio_url
                
        except httpx.HTTPStatusError as e:
            logger.warning(f"Hume.ai TTS may not be available: {e.response.status_code}")
            # TTS might not be available, return None
            return None
        except Exception as e:
            logger.warning(f"Error synthesizing text with Hume.ai: {str(e)}")
            return None
