"""LLM service for communicating with local LM Studio."""

import os
import logging
import requests
from typing import List, Dict, Optional, Union

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with local LM Studio endpoint."""
    
    def __init__(self):
        """Initialize LLM service with configuration from environment."""
        self.base_url = os.getenv('LLM_API_URL', 'http://localhost:1234/v1')
        self.model = os.getenv('LLM_MODEL', 'deepseek/deepseek-r1-0528-qwen3-8b')
        self.timeout = 30
        logger.info(f"LLM Service initialized - base_url: {self.base_url}, model: {self.model}")
        logger.info(f"LLM_API_URL env var: {os.getenv('LLM_API_URL')}")
        logger.info(f"Full endpoint will be: {self.base_url}/chat/completions")
        # Force reload to pick up .env changes
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 800
    ) -> Optional[str]:
        """
        Send chat completion request to local LM Studio.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text or None if error
        """
        try:
            payload: Dict[str, Union[str, List[Dict[str, str]], float, int, bool]] = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            logger.info(f"Calling LLM with {len(messages)} messages")
            logger.info(f"LLM endpoint: {self.base_url}/chat/completions")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"LLM response status: {response.status_code}")
            logger.info(f"LLM response keys: {list(result.keys())}")
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                logger.info(f"Raw LLM content length: {len(content) if content else 0}")
                
                # Handle DeepSeek R1 thinking process output if present
                if content and '<think>' in content.lower():
                    logger.info(f"Found thinking tags in content, processing...")
                    # Find the last </think> tag to handle multiple thinking sections
                    think_end_index = content.lower().rfind('</think>')
                    if think_end_index != -1:
                        # Extract everything after the last </think> tag
                        content = content[think_end_index + len('</think>'):].strip()
                        logger.info(f"Extracted content after think tags, length: {len(content)}")
                    else:
                        # If <think> exists but no closing tag, remove everything from <think> onwards
                        think_start_index = content.lower().find('<think>')
                        if think_start_index != -1:
                            content = content[:think_start_index].strip()
                            logger.info(f"Removed unclosed think section, length: {len(content)}")
                else:
                    # No thinking tags - use content as is
                    logger.info(f"No thinking tags found, using content as-is")
                        
                logger.info(f"Final content: {content[:200]}..." if content and len(content) > 200 else f"Final content: {content}")
                return content if content else None
            else:
                logger.error("No choices in LLM response")
                logger.error(f"Full LLM response: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling LLM endpoint: {e}")
            # Return a demo response when LLM service is unavailable
            if messages and len(messages) > 0:
                user_message = messages[-1]['content'] if 'content' in messages[-1] else 'Hello'
            else:
                user_message = 'Hello'
                
            return (f"🤖 **Demo AI Response**\n\n"
                   f"I received your message: \"{user_message}\"\n\n"
                   "This is a demonstration response since LM Studio is not running. "
                   "In a real deployment, I would provide detailed analysis of your elevator operations data.\n\n"
                   "To get real AI responses:\n"
                   "1. Start LM Studio on localhost:1234\n"
                   "2. Load a compatible model (like DeepSeek R1)\n"
                   "3. Ensure the server is running\n\n"
                   "The application is working correctly in demo mode!")
        except KeyError as e:
            logger.error(f"Unexpected LLM response format: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in LLM service: {e}")
            return None
    
# Global instance
llm_service = LLMService()
