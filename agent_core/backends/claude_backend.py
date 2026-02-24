"""
Claude (Anthropic) AI Backend

Implementation of AI backend using Anthropic's Claude API.
"""

import os
from typing import Optional, Dict, Any
from agent_core.ai_backend import AIBackend, AIResponse, WebSearchResult, AIBackendError


class ClaudeBackend(AIBackend):
    """
    Claude AI backend implementation
    
    Requires:
    - anthropic package installed
    - ANTHROPIC_API_KEY environment variable set
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Claude backend
        
        Args:
            config: Configuration dict with:
                - api_key: Anthropic API key (optional, uses env var if not provided)
                - model: Model name (default: claude-3-sonnet-20240229)
        """
        super().__init__(config)
        self.name = "Claude"
        
        # Get API key from config or environment
        self.api_key = config.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise AIBackendError("ANTHROPIC_API_KEY not found in config or environment")
        
        # Get model name
        self.model = config.get('model', 'claude-3-sonnet-20240229')
        
        # Initialize client
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self._available = True
        except ImportError:
            raise AIBackendError(
                "anthropic package not installed. Install with: pip install anthropic"
            )
        except Exception as e:
            raise AIBackendError(f"Failed to initialize Claude client: {e}")
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None,
                         temperature: float = 0.7, max_tokens: int = 1000) -> AIResponse:
        """
        Generate text response using Claude
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            AIResponse object
        """
        try:
            # Build messages
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # Call Claude API
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = self.client.messages.create(**kwargs)
            
            # Extract content
            content = response.content[0].text if response.content else ""
            
            return AIResponse(
                content=content,
                success=True,
                metadata={
                    "backend": "claude",
                    "model": self.model,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens
                    }
                }
            )
            
        except Exception as e:
            return AIResponse(
                content="",
                success=False,
                error=f"Claude API error: {str(e)}"
            )
    
    def web_search(self, query: str, num_results: int = 5) -> WebSearchResult:
        """
        Perform web search
        
        Note: Claude does not have built-in web search.
        This method raises NotImplementedError.
        
        Args:
            query: Search query
            num_results: Number of results
            
        Returns:
            WebSearchResult object
            
        Raises:
            AIBackendError: Claude does not support web search
        """
        raise AIBackendError("Claude backend does not support web search")
    
    def is_available(self) -> bool:
        """
        Check if Claude backend is available
        
        Returns:
            True if API key is configured and client initialized
        """
        return self._available and self.api_key is not None
    
    def supports_web_search(self) -> bool:
        """Claude does not support web search"""
        return False


if __name__ == '__main__':
    # Test Claude backend
    import sys
    
    print("Testing Claude AI Backend...")
    
    try:
        # Create backend
        config = {
            "model": "claude-3-sonnet-20240229"
        }
        backend = ClaudeBackend(config)
        
        print(f"✓ Backend initialized: {backend.get_name()}")
        print(f"✓ Available: {backend.is_available()}")
        print(f"✓ Supports web search: {backend.supports_web_search()}")
        
        # Test response generation
        print("\nTesting response generation...")
        response = backend.generate_response(
            "What is OBD-II? Answer in one sentence.",
            temperature=0.5,
            max_tokens=100
        )
        
        if response.success:
            print(f"✓ Response: {response.content}")
            print(f"✓ Tokens used: {response.metadata.get('usage', {})}")
        else:
            print(f"✗ Error: {response.error}")
            sys.exit(1)
        
        print("\nClaude backend tests passed!")
        
    except AIBackendError as e:
        print(f"✗ Backend error: {e}")
        print("\nNote: Set ANTHROPIC_API_KEY environment variable to test")
        sys.exit(1)
