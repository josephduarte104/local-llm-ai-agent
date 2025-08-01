"""
Local LLM client for connecting to Ollama or LM Studio
"""

import json
import requests
from typing import Dict, List, Any, Optional
import asyncio
import aiohttp

class LocalLLMClient:
    """
    Client for local LLM services (Ollama, LM Studio)
    """
    
    def __init__(self, provider: str, base_url: str, model: str):
        """Initialize the LLM client"""
        self.provider = provider.lower()
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.session = None
        
    async def initialize(self) -> bool:
        """Initialize the client and test connection"""
        try:
            # Create aiohttp session for async requests
            self.session = aiohttp.ClientSession()
            
            # Test connection
            if self.provider == "ollama":
                return await self._test_ollama_connection()
            elif self.provider == "lmstudio":
                return await self._test_lmstudio_connection()
            else:
                print(f"Unsupported LLM provider: {self.provider}")
                return False
                
        except Exception as e:
            print(f"Failed to initialize LLM client: {e}")
            return False
    
    async def _test_ollama_connection(self) -> bool:
        """Test Ollama connection"""
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    tags_data = await response.json()
                    # Check if our model is available
                    models = [model["name"] for model in tags_data.get("models", [])]
                    if self.model in models:
                        return True
                    else:
                        print(f"Model {self.model} not found in Ollama. Available: {models}")
                        return False
                return False
        except Exception as e:
            print(f"Ollama connection test failed: {e}")
            return False
    
    async def _test_lmstudio_connection(self) -> bool:
        """Test LM Studio connection"""
        try:
            async with self.session.get(f"{self.base_url}/v1/models") as response:
                return response.status == 200
        except Exception as e:
            print(f"LM Studio connection test failed: {e}")
            return False
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Generate a response from the local LLM
        
        Args:
            messages: List of chat messages
            tools: Optional list of available tools
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Dict with response data
        """
        try:
            if self.provider == "ollama":
                return await self._ollama_generate(messages, tools, max_tokens, temperature)
            elif self.provider == "lmstudio":
                return await self._lmstudio_generate(messages, tools, max_tokens, temperature)
            else:
                return {"error": f"Unsupported provider: {self.provider}"}
                
        except Exception as e:
            return {"error": f"Generation failed: {str(e)}"}
    
    async def _ollama_generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]],
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Generate response using Ollama API"""
        
        # Convert messages to Ollama format
        prompt = self._format_messages_for_ollama(messages, tools)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "stop": ["<|im_end|>", "</thinking>"]
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    response_text = result.get("response", "")
                    
                    # Try to extract tool calls if present
                    tool_calls = self._extract_tool_calls(response_text)
                    
                    return {
                        "content": response_text,
                        "tool_calls": tool_calls,
                        "usage": {
                            "prompt_tokens": result.get("prompt_eval_count", 0),
                            "completion_tokens": result.get("eval_count", 0)
                        }
                    }
                else:
                    error_text = await response.text()
                    return {"error": f"Ollama API error {response.status}: {error_text}"}
                    
        except asyncio.TimeoutError:
            return {"error": "Request timeout"}
        except Exception as e:
            return {"error": f"Ollama request failed: {str(e)}"}
    
    async def _lmstudio_generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]],
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Generate response using LM Studio OpenAI-compatible API"""
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        # Add tools if provided
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        try:
            async with self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    choice = result["choices"][0]
                    message = choice["message"]
                    
                    return {
                        "content": message.get("content", ""),
                        "tool_calls": message.get("tool_calls", []),
                        "usage": result.get("usage", {})
                    }
                else:
                    error_text = await response.text()
                    return {"error": f"LM Studio API error {response.status}: {error_text}"}
                    
        except asyncio.TimeoutError:
            return {"error": "Request timeout"}
        except Exception as e:
            return {"error": f"LM Studio request failed: {str(e)}"}
    
    def _format_messages_for_ollama(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]]) -> str:
        """Format messages for Ollama (no native chat format)"""
        formatted = "<|im_start|>system\nYou are an AI assistant that analyzes elevator operations data.\n"
        
        # Add tool information if available
        if tools:
            formatted += "\nYou have access to these tools:\n"
            for tool in tools:
                formatted += f"- {tool['function']['name']}: {tool['function']['description']}\n"
            formatted += "\nTo call a tool, use this format:\n<tool_call>\n{\"name\": \"tool_name\", \"parameters\": {...}}\n</tool_call>\n"
        
        formatted += "<|im_end|>\n"
        
        # Add conversation history
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            formatted += f"<|im_start|>{role}\n{content}<|im_end|>\n"
        
        formatted += "<|im_start|>assistant\n"
        return formatted
    
    def _extract_tool_calls(self, response_text: str) -> List[Dict]:
        """Extract tool calls from response text"""
        tool_calls = []
        
        # Look for tool call patterns
        import re
        pattern = r'<tool_call>\s*({.*?})\s*</tool_call>'
        matches = re.findall(pattern, response_text, re.DOTALL)
        
        for match in matches:
            try:
                call_data = json.loads(match)
                tool_calls.append({
                    "type": "function",
                    "function": {
                        "name": call_data.get("name"),
                        "arguments": json.dumps(call_data.get("parameters", {}))
                    }
                })
            except json.JSONDecodeError:
                continue
        
        return tool_calls
    
    async def close(self):
        """Close the client session"""
        if self.session:
            await self.session.close()

def create_llm_client(provider: str, base_url: str, model: str) -> LocalLLMClient:
    """Factory function to create LLM client"""
    return LocalLLMClient(provider, base_url, model)
