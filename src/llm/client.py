"""
LLM Client for Local Language Models (Ollama/LM Studio)
"""

import asyncio
import aiohttp
import requests
from typing import Dict, Any, Optional
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class LLMClient:
    """Client for interacting with local LLM services"""
    
    def __init__(self, settings):
        self.settings = settings
        self.provider = settings.LLM_PROVIDER
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        if self.provider == "ollama":
            self.base_url = settings.OLLAMA_BASE_URL
            self.model = settings.OLLAMA_MODEL
            self.endpoint = f"{self.base_url}/api/generate"
        elif self.provider == "lmstudio":
            self.base_url = settings.LMSTUDIO_BASE_URL
            self.model = settings.LMSTUDIO_MODEL
            self.endpoint = self.base_url
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def query_sync(self, prompt: str, system_prompt: str = None) -> str:
        """Synchronous query method for Flask app"""
        try:
            if self.provider == "ollama":
                return self._query_ollama_sync(prompt, system_prompt)
            elif self.provider == "lmstudio":
                return self._query_lmstudio_sync(prompt, system_prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return f"Error: {str(e)}"
    
    def _query_ollama_sync(self, prompt: str, system_prompt: str = None) -> str:
        """Query Ollama using synchronous requests"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "No response from Ollama")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            raise Exception(f"Ollama request failed: {e}")
    
    def _query_lmstudio_sync(self, prompt: str, system_prompt: str = None) -> str:
        """Query LM Studio using synchronous requests"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000,  # Increased for chain-of-thought reasoning
            "stream": False
        }
        
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=60,  # Much longer timeout for reasoning models
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                
                # Handle DeepSeek R1 chain-of-thought format
                if content.startswith("<think>"):
                    # Extract the final answer after </think>
                    think_end = content.find("</think>")
                    if think_end != -1:
                        content = content[think_end + 8:].strip()
                    else:
                        # If no closing tag, take everything after <think>
                        content = content[7:].strip()
                
                return content if content else "No response from LM Studio"
            else:
                return "No response from LM Studio"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"LM Studio request failed: {e}")
            raise Exception(f"LM Studio request failed: {e}")
    
    async def query_async(self, prompt: str, system_prompt: str = None) -> str:
        """Async query method for async contexts"""
        try:
            if self.provider == "ollama":
                return await self._query_ollama_async(prompt, system_prompt)
            elif self.provider == "lmstudio":
                return await self._query_lmstudio_async(prompt, system_prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            logger.error(f"Async LLM query failed: {e}")
            return f"Error: {str(e)}"
    
    async def _query_ollama_async(self, prompt: str, system_prompt: str = None) -> str:
        """Query Ollama using async requests"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.endpoint,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result.get("response", "No response from Ollama")
                    
            except aiohttp.ClientError as e:
                logger.error(f"Async Ollama request failed: {e}")
                raise Exception(f"Async Ollama request failed: {e}")
    
    async def _query_lmstudio_async(self, prompt: str, system_prompt: str = None) -> str:
        """Query LM Studio using async requests"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.endpoint,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    else:
                        return "No response from LM Studio"
                        
            except aiohttp.ClientError as e:
                logger.error(f"Async LM Studio request failed: {e}")
                raise Exception(f"Async LM Studio request failed: {e}")
    
    def query(self, prompt: str, system_prompt: str = None) -> str:
        """Main query method - automatically chooses sync or async based on context"""
        try:
            # Try to get current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, but need to run sync
                # Use thread executor to avoid blocking
                future = self.executor.submit(self.query_sync, prompt, system_prompt)
                return future.result(timeout=35)
            else:
                # No running loop, use sync
                return self.query_sync(prompt, system_prompt)
        except RuntimeError:
            # No event loop, use sync
            return self.query_sync(prompt, system_prompt)
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return f"Error: {str(e)}"
    
    def test_connection(self) -> bool:
        """Test connection to LLM service"""
        try:
            response = self.query_sync("Test connection - respond with 'OK'")
            return "ok" in response.lower()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
