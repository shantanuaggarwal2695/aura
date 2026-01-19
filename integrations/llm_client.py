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
        model_name: str = "gemini-pro",
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
                - Gemini: gemini-pro, gemini-1.5-pro, etc.
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
            conversation_history = conversation_history or []
            
            # Build messages array for Gemini API
            messages = []
            
            # Add conversation history
            for msg in conversation_history[-10:]:  # Limit to last 10 messages
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
            
            # Build Gemini API URL
            url = f"{self.api_url}/models/{self.model_name}:generateContent"
            if self.api_key:
                url += f"?key={self.api_key}"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = {"Content-Type": "application/json"}
                response = await client.post(url, json=payload, headers=headers)
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
            logger.error(f"Gemini API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Gemini API error: {e.response.status_code}")
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
