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
        # Check which LLM provider is configured
        provider = os.getenv('LLM_PROVIDER', 'lmstudio').lower()
        
        if provider == 'lmstudio':
            # Use LM Studio configuration from .env
            base_url = os.getenv('LMSTUDIO_BASE_URL', 'http://127.0.0.1:1234/v1/chat/completions')
            # If the URL already includes /chat/completions, use it as-is
            # Otherwise, ensure it ends with /v1 so we can append /chat/completions later
            if base_url.endswith('/chat/completions'):
                self.chat_url = base_url
                self.base_url = base_url.replace('/chat/completions', '/v1')
            else:
                if not base_url.endswith('/v1'):
                    base_url = base_url.rstrip('/') + '/v1'
                self.base_url = base_url
                self.chat_url = base_url + '/chat/completions'
            self.model = os.getenv('LMSTUDIO_MODEL', 'liquid/lfm2-1.2b')
        elif provider == 'ollama':
            # Use Ollama configuration from .env
            self.base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
            self.chat_url = self.base_url + '/api/chat'
            self.model = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')
        else:
            # Fallback to legacy environment variables
            self.base_url = os.getenv('LLM_API_URL', 'http://localhost:1234/v1')
            self.chat_url = self.base_url + '/chat/completions'
            self.model = os.getenv('LLM_MODEL', 'deepseek/deepseek-r1-0528-qwen3-8b')
        
        self.timeout = 30
        logger.info(f"LLM Service initialized - provider: {provider}")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Chat URL: {self.chat_url}")
        logger.info(f"Model: {self.model}")
    
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
            logger.info(f"LLM endpoint: {self.chat_url}")
            
            response = requests.post(
                self.chat_url,
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
                
                # Handle thinking process output - both tagged and untagged reasoning
                content = self._extract_final_response(content)
                logger.info(f"Processed content length: {len(content) if content else 0}")
                        
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
    
    def _extract_final_response(self, content: str) -> str:
        """
        Extract the final response from LLM content, removing thinking/reasoning sections.
        
        Handles both tagged thinking (<think>...</think>) and untagged reasoning patterns.
        """
        if not content:
            return content
        
        # First, handle formal thinking tags
        if '<think>' in content.lower():
            logger.info("Found formal thinking tags, processing...")
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
        
        # Handle untagged reasoning patterns
        content = self._filter_reasoning_text(content)
        
        return content
    
    def _filter_reasoning_text(self, content: str) -> str:
        """
        Filter out untagged reasoning text that appears before the actual response.
        
        Detects common reasoning patterns and extracts the formatted response.
        """
        if not content:
            return content
        
        lines = content.split('\n')
        
        # Look for reasoning indicators at the start
        reasoning_patterns = [
            'we need',
            'let\'s',
            'provide insights',
            'compute',
            'calculate',
            'we can',
            'let me',
            'i need to',
            'first,',
            'analysis:',
            'calculation:',
            'reasoning:',
            'total cycles overall',  # Specific pattern from logs
            'elevator1:',           # Calculation patterns
            'elevator2:',
            'reversals totals:',
            'average opened duration:',
            'also mention',
            'provide totals',
            'let\'s craft'
        ]
        
        # Look for the start of the actual formatted response
        response_indicators = [
            '# ',      # Markdown header
            '## ',     # Markdown header
            '### ',    # Markdown header
            '**',      # Bold text
            '|',       # Table
            '```',     # Code block
            '- ',      # List item
            '1. ',     # Numbered list
            '* ',      # List item
            '+ ',      # List item
        ]
        
        # Find the transition from reasoning to response
        reasoning_end_idx = 0
        response_start_idx = -1
        
        for i, line in enumerate(lines):
            line_lower = line.strip().lower()
            
            # Skip empty lines
            if not line_lower:
                continue
            
            # Check if this line looks like reasoning
            is_reasoning = any(pattern in line_lower for pattern in reasoning_patterns)
            
            # Check if this line looks like formatted response
            is_response = any(line.strip().startswith(indicator) for indicator in response_indicators)
            
            if is_reasoning and response_start_idx == -1:
                reasoning_end_idx = i + 1
            elif is_response and response_start_idx == -1:
                response_start_idx = i
                break
            elif not is_reasoning and not is_response and response_start_idx == -1:
                # Found non-reasoning, non-response text - could be start of response
                if len(line.strip()) > 10:  # Ignore very short lines
                    response_start_idx = i
                    break
        
        # If we found a clear response start, use it
        if response_start_idx >= 0:
            filtered_content = '\n'.join(lines[response_start_idx:]).strip()
            if filtered_content:
                logger.info(f"Filtered reasoning text, extracted response from line {response_start_idx}")
                return filtered_content
        
        # If no clear pattern found, look for content after "Let's craft response" or similar
        craft_patterns = [
            'let\'s craft response',
            'response:',
            'final response:',
            'here\'s the response:',
            'answer:',
            'result:',
            'let\'s craft',
            'craft response'
        ]
        
        # Special case: Look for reasoning followed by "###" which indicates start of markdown
        hash_pattern_idx = content.find('###')
        if hash_pattern_idx != -1:
            # Check if there's reasoning text before the ###
            before_hash = content[:hash_pattern_idx].strip()
            if before_hash and any(pattern in before_hash.lower() for pattern in reasoning_patterns):
                after_hash = content[hash_pattern_idx:].strip()
                if after_hash:
                    logger.info("Found reasoning followed by markdown header, extracting from ###")
                    return after_hash
        
        content_lower = content.lower()
        for pattern in craft_patterns:
            pattern_idx = content_lower.find(pattern)
            if pattern_idx != -1:
                # Find the end of the line containing the pattern
                line_end = content.find('\n', pattern_idx)
                if line_end != -1:
                    after_pattern = content[line_end:].strip()
                    if after_pattern:
                        logger.info(f"Found craft pattern '{pattern}', extracting content after")
                        return after_pattern
        
        # If no patterns detected, check if content looks like reasoning vs response
        # If it starts with reasoning language but contains markdown, extract the markdown parts
        if any(pattern in content.lower()[:200] for pattern in reasoning_patterns):
            # Look for markdown sections
            markdown_lines = []
            in_markdown = False
            
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    if in_markdown:
                        markdown_lines.append(line)
                    continue
                
                # Check if this line is markdown-formatted
                is_markdown = (
                    line_stripped.startswith('#') or 
                    line_stripped.startswith('|') or
                    line_stripped.startswith('```') or
                    line_stripped.startswith('**') or
                    line_stripped.startswith('- ') or
                    line_stripped.startswith('* ') or
                    line_stripped.startswith('+ ') or
                    any(char.isdigit() and line_stripped.startswith(f'{char}. ') for char in '123456789')
                )
                
                if is_markdown:
                    in_markdown = True
                    markdown_lines.append(line)
                elif in_markdown:
                    # Continue collecting if we're in a markdown section
                    markdown_lines.append(line)
                elif not any(pattern in line.lower() for pattern in reasoning_patterns):
                    # Not reasoning and not markdown, might be regular response text
                    if in_markdown or len(markdown_lines) == 0:
                        markdown_lines.append(line)
            
            markdown_content = '\n'.join(markdown_lines).strip()
            if markdown_content and len(markdown_content) > len(content) * 0.3:  # At least 30% of original
                logger.info("Extracted markdown/formatted sections from mixed content")
                return markdown_content
        
        # If no filtering was applied, return original content
        logger.info("No reasoning patterns detected, using original content")
        return content

# Global instance
llm_service = LLMService()
