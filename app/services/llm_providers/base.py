"""
Base LLM Provider Interface
Tương đương với Interface trong Laravel/PHP
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Iterator, Union


class LLMProvider(ABC):
    """
    Abstract base class cho LLM providers
    Tất cả providers phải implement các methods này
    """
    
    @abstractmethod
    def embed(
        self, 
        prompt: Union[str, List[str]], 
        model: Optional[str] = None
    ) -> Union[List[float], List[List[float]]]:
        """
        Generate embedding(s) từ text
        
        Args:
            prompt: Single text hoặc list of texts
            model: Model name (optional)
            
        Returns:
            Single embedding (list of floats) hoặc list of embeddings
        """
        pass
    
    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Union[Dict, Iterator[Dict]]:
        """
        Chat với LLM
        
        Args:
            messages: List of message dicts [{'role': 'user', 'content': '...'}, ...]
            model: Model name (optional)
            stream: Whether to stream response
            temperature: Temperature for response (0.0-2.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict với response nếu stream=False
            Iterator of dicts nếu stream=True
        """
        pass
    
    @abstractmethod
    def list_models(self) -> List[Dict]:
        """
        List available models from this provider
        
        Returns:
            List of model dicts with 'id', 'name', etc.
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name (e.g., 'ollama', 'openai')"""
        pass


class LLMProviderFactory:
    """
    Factory để tạo LLM provider instances
    Tương đương với Factory Pattern trong Laravel
    """
    
    _providers = {}
    
    @classmethod
    def register(cls, provider_name: str, provider_class: type):
        """Register a provider class"""
        cls._providers[provider_name] = provider_class
    
    @classmethod
    def create(cls, provider_name: str, **kwargs) -> LLMProvider:
        """
        Create a provider instance
        
        Args:
            provider_name: 'ollama', 'openai', 'anthropic', 'deepseek', etc.
            **kwargs: Provider-specific configuration
                     For LiteLLMProvider, should include provider_name in kwargs
            
        Returns:
            LLMProvider instance
            
        Raises:
            ValueError: If provider not found
        """
        if provider_name not in cls._providers:
            raise ValueError(
                f"Provider '{provider_name}' not found. "
                f"Available: {list(cls._providers.keys())}"
            )
        
        provider_class = cls._providers[provider_name]
        # For LiteLLMProvider, always pass provider_name
        # Remove if already exists to avoid duplicate
        kwargs.pop('provider_name', None)
        kwargs['provider_name'] = provider_name
        return provider_class(**kwargs)
    
    @classmethod
    def get_default(cls) -> LLMProvider:
        """Get default provider (from settings)"""
        from django.conf import settings
        provider_name = getattr(settings, 'DEFAULT_LLM_PROVIDER', 'ollama')
        return cls.create(provider_name)

