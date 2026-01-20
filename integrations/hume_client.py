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
        
        # Log API key status (masked)
        def mask_key(key: str) -> str:
            if not key:
                return "NOT_SET"
            if len(key) <= 8:
                return "***"
            return f"{key[:4]}...{key[-4:]}"
        
        logger.info(f"HumeClient initialized - API Key: {mask_key(api_key)}, URL: {self.api_url}")
        
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe audio to text using Hume.ai speech-to-text.
        
        Note: Hume.ai EVI (Empathic Voice Interface) requires a Configuration ID
        and is designed for real-time conversation, not simple transcription.
        
        This implementation attempts to use Hume's batch transcription API if available,
        otherwise falls back to a placeholder that indicates the limitation.
        
        Args:
            audio_data: Raw audio bytes (WAV, MP3, etc.)
            
        Returns:
            Transcribed text string
            
        Raises:
            Exception: If transcription fails or Hume.ai doesn't support simple transcription
        """
        try:
            # Hume.ai EVI is designed for conversational AI, not simple transcription
            # The /v0/evi/transcriptions endpoint doesn't exist
            # For simple transcription, you may need to:
            # 1. Use a different service (e.g., Google Speech-to-Text, OpenAI Whisper)
            # 2. Use browser's Web Speech API (already implemented in frontend)
            # 3. Use Hume's batch processing API if available
            
            # Try alternative endpoints that might exist
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Option 1: Try batch transcription endpoint (if it exists)
                url = f"{self.api_url}/v0/batch/transcriptions"
                
                files = {
                    "audio": ("audio.wav", audio_data, "audio/wav")
                }
                
                headers = {
                    "X-Hume-Api-Key": self.api_key
                }
                
                try:
                    response = await client.post(
                        url,
                        files=files,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        transcription = result.get("transcription", "") or result.get("text", "") or result.get("transcript", "")
                        
                        if transcription:
                            logger.info(f"Successfully transcribed audio: {transcription[:50]}...")
                            return transcription
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        logger.warning(f"Hume.ai batch transcription endpoint not found (404). Trying alternative...")
                    else:
                        raise
                
                # Option 2: Try jobs API (if available)
                url = f"{self.api_url}/v0/jobs"
                
                try:
                    # Create a job for transcription
                    job_response = await client.post(
                        url,
                        files=files,
                        headers=headers
                    )
                    
                    if job_response.status_code == 200:
                        job_result = job_response.json()
                        job_id = job_result.get("job_id") or job_result.get("id")
                        
                        if job_id:
                            # Poll for job completion
                            job_url = f"{self.api_url}/v0/jobs/{job_id}"
                            import asyncio
                            
                            for _ in range(10):  # Poll up to 10 times
                                await asyncio.sleep(1)
                                status_response = await client.get(job_url, headers=headers)
                                
                                if status_response.status_code == 200:
                                    status_data = status_response.json()
                                    if status_data.get("status") == "completed":
                                        transcription = status_data.get("transcription", "") or status_data.get("text", "")
                                        if transcription:
                                            logger.info(f"Successfully transcribed audio via job: {transcription[:50]}...")
                                            return transcription
                                    elif status_data.get("status") == "failed":
                                        break
                        
                except httpx.HTTPStatusError:
                    pass  # Jobs API might not exist either
                
                # If all endpoints fail, raise informative error
                raise Exception(
                    "Hume.ai does not provide a simple transcription endpoint. "
                    "Hume.ai EVI is designed for conversational AI with Configuration IDs. "
                    "For simple speech-to-text, consider using:\n"
                    "1. Browser's Web Speech API (already available in frontend)\n"
                    "2. Google Cloud Speech-to-Text API\n"
                    "3. OpenAI Whisper API\n"
                    "4. AssemblyAI or other transcription services"
                )
                
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_response = e.response.json()
                error_detail = error_response.get("detail", "") or error_response.get("message", "")
            except:
                error_detail = e.response.text[:200] if e.response.text else ""
            
            logger.error(f"Hume.ai API error: {e.response.status_code} - {error_detail}")
            raise Exception(
                f"Hume.ai API error ({e.response.status_code}): "
                f"Hume.ai EVI is designed for conversational AI, not simple transcription. "
                f"Please use the browser's built-in Web Speech API or configure a different transcription service. "
                f"Error details: {error_detail}"
            )
        except Exception as e:
            if "does not provide" in str(e) or "Hume.ai EVI" in str(e):
                raise  # Re-raise informative errors
            logger.error(f"Error transcribing audio with Hume.ai: {str(e)}", exc_info=True)
            raise Exception(f"Error transcribing audio: {str(e)}")
    
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
