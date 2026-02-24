"""
AI Backend Interface

Abstract interface for AI backend implementations.
Supports multiple AI providers: OpenAI, Claude, Ollama, etc.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class AIResponse:
    """Response from AI backend"""
    content: str
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WebSearchResult:
    """Web search result from AI backend"""
    query: str
    results: List[Dict[str, str]]
    success: bool
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []


class AIBackendError(Exception):
    """AI backend error"""
    pass


class AIBackend(ABC):
    """
    Abstract base class for AI backends
    
    Implementations must provide:
    - generate_response(): Generate text response from prompt
    - web_search(): Perform web search (if supported)
    - is_available(): Check if backend is available
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize AI backend
        
        Args:
            config: Configuration dict with backend-specific settings
        """
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None,
                         temperature: float = 0.7, max_tokens: int = 1000) -> AIResponse:
        """
        Generate text response from prompt
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            AIResponse object
            
        Raises:
            AIBackendError: If generation fails
        """
        pass
    
    @abstractmethod
    def web_search(self, query: str, num_results: int = 5) -> WebSearchResult:
        """
        Perform web search
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            WebSearchResult object
            
        Raises:
            AIBackendError: If search fails or not supported
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if backend is available
        
        Returns:
            True if backend can be used
        """
        pass
    
    def get_name(self) -> str:
        """Get backend name"""
        return self.name
    
    def supports_web_search(self) -> bool:
        """
        Check if backend supports web search
        
        Returns:
            True if web search is supported
        """
        # Default implementation - can be overridden
        try:
            # Try a test search
            result = self.web_search("test", num_results=1)
            return result.success
        except (AIBackendError, NotImplementedError):
            return False


class MockAIBackend(AIBackend):
    """
    Mock AI backend for testing
    
    Returns predefined responses without calling external APIs
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize mock backend"""
        super().__init__(config or {})
        self.name = "MockAI"
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None,
                         temperature: float = 0.7, max_tokens: int = 1000) -> AIResponse:
        """Generate mock response"""
        return AIResponse(
            content=f"Mock response to: {prompt[:50]}...",
            success=True,
            metadata={"backend": "mock", "prompt_length": len(prompt)}
        )
    
    def web_search(self, query: str, num_results: int = 5) -> WebSearchResult:
        """Perform mock web search"""
        return WebSearchResult(
            query=query,
            results=[
                {
                    "title": f"Mock result for {query}",
                    "url": "https://example.com",
                    "snippet": "This is a mock search result"
                }
            ],
            success=True
        )
    
    def is_available(self) -> bool:
        """Mock backend is always available"""
        return True


def create_backend(backend_type: str, config: Dict[str, Any]) -> AIBackend:
    """
    Factory function to create AI backend
    
    Args:
        backend_type: Backend type ("openai", "claude", "ollama", "mock")
        config: Configuration dict
        
    Returns:
        AIBackend instance
        
    Raises:
        ValueError: If backend type is unknown
    """
    backend_type = backend_type.lower()
    
    if backend_type == "mock":
        return MockAIBackend(config)
    elif backend_type == "openai":
        from agent_core.backends.openai_backend import OpenAIBackend
        return OpenAIBackend(config)
    elif backend_type == "claude":
        from agent_core.backends.claude_backend import ClaudeBackend
        return ClaudeBackend(config)
    elif backend_type == "ollama":
        from agent_core.backends.ollama_backend import OllamaBackend
        return OllamaBackend(config)
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")


if __name__ == '__main__':
    # Test mock backend
    print("Testing Mock AI Backend...")
    
    backend = MockAIBackend()
    
    # Test response generation
    response = backend.generate_response("What is OBD-II?")
    print(f"✓ Generated response: {response.content}")
    
    # Test web search
    search_result = backend.web_search("Ford Escape HVAC diagnostics")
    print(f"✓ Search results: {len(search_result.results)} found")
    
    # Test availability
    print(f"✓ Backend available: {backend.is_available()}")
    
    print("\nMock backend tests passed!")
