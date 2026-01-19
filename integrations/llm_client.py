"""
Unified LLM client supporting multiple providers including open-source models.
Supports: Google Gemini, OpenAI-compatible APIs (Ollama, vLLM, Together AI, etc.)
"""

import logging
import httpx
from typing import List, Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"
    OPENAI_COMPATIBLE = "openai_compatible"  # For Ollama, vLLM, Together AI, etc.
    HUGGINGFACE = "huggingface"


class LLMClient:
    """Unified client for interacting with various LLM providers including open-source models."""
    
    def __init__(
        self, 
        provider: str = "gemini",
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model_name: str = "gemini-2.5-flash-lite",
        system_instruction: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize LLM client.
        
        Args:
            provider: Provider type - "gemini", "openai_compatible", or "huggingface"
            api_key: API key for the provider (optional for local models)
            api_url: Base URL for the API endpoint
                - Gemini: https://generativelanguage.googleapis.com/v1beta
                - OpenAI-compatible: http://localhost:11434/v1 (Ollama) or custom endpoint
                - Hugging Face: https://api-inference.huggingface.co
            model_name: Name of the model to use
                - Gemini: gemini-2.5-flash-lite (recommended), gemini-2.5-flash, gemini-1.5-pro, etc.
                - OpenAI-compatible: llama3.2, mistral, etc. (depends on provider)
                - Hugging Face: meta-llama/Llama-3.2-3B-Instruct, etc.
            system_instruction: System prompt/instruction for the AI agent
            **kwargs: Additional provider-specific arguments
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.api_url = api_url
        self.model_name = model_name
        self.system_instruction = system_instruction
        
        # Set default URLs based on provider
        if not self.api_url:
            if self.provider == "gemini":
                self.api_url = "https://generativelanguage.googleapis.com/v1beta"
            elif self.provider == "openai_compatible":
                self.api_url = "http://localhost:11434/v1"  # Default Ollama
            elif self.provider == "huggingface":
                self.api_url = "https://api-inference.huggingface.co"
        
        # Provider-specific config
        self.kwargs = kwargs
        
        # Log configuration (mask API key)
        def mask_key(key: Optional[str]) -> str:
            if not key:
                return "NOT_SET"
            if len(key) <= 8:
                return "***"
            return f"{key[:4]}...{key[-4:]}"
        
        logger.info(f"LLMClient initialized - Provider: {self.provider}, Model: {self.model_name}, API Key: {mask_key(self.api_key)}, URL: {self.api_url}")
        
    async def get_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Get AI response from the configured LLM provider.
        
        Args:
            message: User's message/query
            conversation_history: Previous conversation messages for context
                Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            
        Returns:
            AI-generated response string
        """
        if self.provider == "gemini":
            return await self._get_gemini_response(message, conversation_history)
        elif self.provider == "openai_compatible":
            return await self._get_openai_compatible_response(message, conversation_history)
        elif self.provider == "huggingface":
            return await self._get_huggingface_response(message, conversation_history)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def _get_gemini_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> str:
        """Get response from Google Gemini API."""
        try:
            # Validate inputs
            if not message or not message.strip():
                raise ValueError("Message cannot be empty")
            
            if not self.api_key:
                logger.error("Gemini API key is not configured")
                raise ValueError("Gemini API key is not configured. Please set GOOGLE_ADK_API_KEY or LLM_API_KEY in your .env file")
            
            # Log API key status (masked)
            def mask_key(key: str) -> str:
                if len(key) <= 8:
                    return "***"
                return f"{key[:4]}...{key[-4:]}"
            
            logger.debug(f"Using Gemini API key: {mask_key(self.api_key)}")
            
            conversation_history = conversation_history or []
            
            # Build messages array for Gemini API
            messages = []
            
            # Add conversation history
            # Note: Gemini API uses "model" for assistant responses, not "assistant"
            for msg in conversation_history[-10:]:  # Limit to last 10 messages
                role = msg.get("role", "user")
                content = msg.get("content", "").strip()
                if content:  # Only add non-empty messages
                    # Convert "assistant" to "model" for Gemini API
                    gemini_role = "model" if role == "assistant" else "user"
                    messages.append({
                        "role": gemini_role,
                        "parts": [{"text": content}]
                    })
            
            # Add current user message
            messages.append({
                "role": "user",
                "parts": [{"text": message.strip()}]
            })
            
            # Validate we have at least one message
            if not messages:
                raise ValueError("No messages to send")
            
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
            if self.system_instruction and self.system_instruction.strip():
                payload["systemInstruction"] = {
                    "parts": [{"text": self.system_instruction.strip()}]
                }
            
            # Build Gemini API URL
            # Note: Gemini API expects model names like "gemini-pro" or "gemini-1.5-pro"
            # Make sure model name is valid
            url = f"{self.api_url}/models/{self.model_name}:generateContent"
            if self.api_key:
                url += f"?key={self.api_key}"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = {"Content-Type": "application/json"}
                
                # Log request for debugging (without sensitive data)
                logger.debug(f"Gemini API request: URL={url.split('?')[0]}, model={self.model_name}, messages={len(messages)}")
                
                response = await client.post(url, json=payload, headers=headers)
                
                # Log response status
                logger.debug(f"Gemini API response: status={response.status_code}")
                
                response.raise_for_status()
                result = response.json()
                
                # Extract response text
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if len(parts) > 0 and "text" in parts[0]:
                            return parts[0]["text"]
                
                raise ValueError("Could not parse Gemini response")
                
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_response = e.response.json()
                if "error" in error_response:
                    error_detail = error_response["error"].get("message", str(error_response["error"]))
                else:
                    error_detail = e.response.text
            except:
                error_detail = e.response.text
            
            logger.error(f"Gemini API error: {e.response.status_code} - {error_detail}")
            logger.error(f"Attempted to use model: {self.model_name}")
            
            # Provide helpful suggestions for common errors
            if e.response.status_code == 404 and "not found" in error_detail.lower():
                suggestion = (
                    f"\n❌ The model '{self.model_name}' is not available in API version v1beta.\n\n"
                    f"✅ Try using one of these available models:\n"
                    f"   - gemini-2.5-flash-lite (recommended - latest, fast, efficient)\n"
                    f"   - gemini-2.5-flash\n"
                    f"   - gemini-1.5-pro\n"
                    f"   - gemini-1.5-pro-latest\n\n"
                    f"📝 Update GOOGLE_ADK_MODEL_NAME in your .env file:\n"
                    f"   GOOGLE_ADK_MODEL_NAME=gemini-2.5-flash-lite\n\n"
                    f"Then restart your application."
                )
                error_detail += suggestion
                logger.error(suggestion)
            
            raise Exception(f"Gemini API error ({e.response.status_code}): {error_detail}")
        except Exception as e:
            logger.error(f"Error getting Gemini response: {str(e)}", exc_info=True)
            raise
    
    async def _get_openai_compatible_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> str:
        """Get response from OpenAI-compatible API (Ollama, vLLM, Together AI, etc.)."""
        try:
            conversation_history = conversation_history or []
            
            # Build messages array (OpenAI format)
            messages = []
            
            # Add system instruction if configured
            if self.system_instruction:
                messages.append({
                    "role": "system",
                    "content": self.system_instruction
                })
            
            # Add conversation history
            for msg in conversation_history[-10:]:  # Limit to last 10 messages
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Prepare request payload (OpenAI-compatible format)
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024,
            }
            
            # Build API URL
            url = f"{self.api_url.rstrip('/')}/chat/completions"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                
                # Extract response text (OpenAI format)
                if "choices" in result and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
                
                raise ValueError("Could not parse OpenAI-compatible response")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI-compatible API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting OpenAI-compatible response: {str(e)}", exc_info=True)
            raise
    
    async def _get_huggingface_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> str:
        """Get response from Hugging Face Inference API."""
        try:
            conversation_history = conversation_history or []
            
            # Build conversation text
            conversation_text = ""
            if self.system_instruction:
                conversation_text += f"System: {self.system_instruction}\n\n"
            
            # Add conversation history
            for msg in conversation_history[-5:]:  # Limit to last 5 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                conversation_text += f"{role.capitalize()}: {content}\n"
            
            # Add current user message
            conversation_text += f"User: {message}\nAssistant:"
            
            # Prepare request payload
            payload = {
                "inputs": conversation_text,
                "parameters": {
                    "temperature": 0.7,
                    "max_new_tokens": 1024,
                    "return_full_text": False
                }
            }
            
            # Build API URL
            url = f"{self.api_url.rstrip('/')}/models/{self.model_name}"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                
                # Extract response text (Hugging Face format)
                if isinstance(result, list) and len(result) > 0:
                    if "generated_text" in result[0]:
                        return result[0]["generated_text"].strip()
                    elif "text" in result[0]:
                        return result[0]["text"].strip()
                
                # Fallback: try to extract from any text field
                if isinstance(result, dict) and "generated_text" in result:
                    return result["generated_text"].strip()
                
                raise ValueError("Could not parse Hugging Face response")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Hugging Face API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Hugging Face API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting Hugging Face response: {str(e)}", exc_info=True)
            raise


# Backward compatibility alias
GoogleADKClient = LLMClient
