"""
Google ADK (Agentic AI) client for processing user queries and generating responses.
"""

import logging
import httpx
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class GoogleADKClient:
    """Client for interacting with Google ADK (Agentic AI) API."""
    
    def __init__(
        self, 
        api_key: str, 
        api_url: str = "https://generativelanguage.googleapis.com/v1beta",
        system_instruction: Optional[str] = None,
        model_name: str = "gemini-pro"
    ):
        """
        Initialize Google ADK client.
        
        Args:
            api_key: Google ADK API key
            api_url: Base URL for Google ADK API
            system_instruction: System prompt/instruction for the AI agent
                This defines the agent's behavior, personality, and capabilities
            model_name: Name of the Gemini model to use
                Options: gemini-pro, gemini-1.5-pro, gemini-1.5-flash, 
                        gemini-2.0-flash, gemini-pro-vision (multimodal)
        """
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.system_instruction = system_instruction
        self.model_name = model_name
        
    async def get_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Get AI response from Google ADK for a user message.
        
        Args:
            message: User's message/query
            conversation_history: Previous conversation messages for context
                Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            
        Returns:
            AI-generated response string
            
        Note:
            This implementation uses Google's Generative AI API (Gemini).
            Adjust the endpoint and model name based on your specific Google ADK setup.
        """
        try:
            conversation_history = conversation_history or []
            
            # Build messages array for the API
            messages = []
            
            # Add conversation history
            for msg in conversation_history[-10:]:  # Limit to last 10 messages for context
                messages.append({
                    "role": msg.get("role", "user"),
                    "parts": [{"text": msg.get("content", "")}]
                })
            
            # Add current user message
            messages.append({
                "role": "user",
                "parts": [{"text": message}]
            })
            
            # Prepare request payload
            payload = {
                "contents": messages,
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }
            
            # Add system instruction if configured
            if self.system_instruction:
                payload["systemInstruction"] = {
                    "parts": [{"text": self.system_instruction}]
                }
            
            # Use Gemini API endpoint with configured model
            url = f"{self.api_url}/models/{self.model_name}:generateContent?key={self.api_key}"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Extract response text
                # Adjust based on actual Google ADK response structure
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if len(parts) > 0 and "text" in parts[0]:
                            ai_response = parts[0]["text"]
                            logger.info(f"Successfully generated AI response: {ai_response[:50]}...")
                            return ai_response
                
                # Fallback parsing
                if "text" in result:
                    return result["text"]
                
                logger.warning("Unexpected response structure from Google ADK")
                raise ValueError("Could not parse response from Google ADK")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Google ADK API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Google ADK API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Error getting response from Google ADK: {str(e)}", exc_info=True)
            raise
