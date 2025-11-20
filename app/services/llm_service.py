"""
LLM Service - High-level service để interact với LLM providers
Tương đương với Service Layer trong Laravel

Sử dụng LLMProviderFactory để get provider based on session/model config
"""

from typing import List, Dict, Optional, Iterator, Union
from django.conf import settings
from .llm_providers import LLMProviderFactory, LLMProvider


def get_llm_provider(provider_name: Optional[str] = None) -> LLMProvider:
    """
    Get LLM provider instance
    Tương đương với dependency injection trong Laravel
    
    Args:
        provider_name: 'ollama', 'openai', 'deepseek', etc.
                      If None, uses default from settings or session
    
    Returns:
        LLMProvider instance
    """
    if provider_name:
        # LLMProviderFactory.create() will pass provider_name to constructor
        return LLMProviderFactory.create(provider_name)
    
    # Use default from settings
    from django.conf import settings
    default_provider = getattr(settings, 'DEFAULT_LLM_PROVIDER', 'ollama')
    return LLMProviderFactory.create(default_provider)


def get_provider_for_session(session) -> LLMProvider:
    """
    Get LLM provider for a ChatSession
    Uses session.model_provider to determine which provider to use
    
    Args:
        session: ChatSession instance
    
    Returns:
        LLMProvider instance configured for this session
    """
    provider_name = session.model_provider if session else 'ollama'
    # LLMProviderFactory.create() will pass provider_name to constructor
    return LLMProviderFactory.create(provider_name)


# Convenience functions (backward compatibility)
def embed(prompt: Union[str, List[str]], model: Optional[str] = None, provider: Optional[str] = None) -> Union[List[float], List[List[float]]]:
    """
    Generate embedding(s) using default or specified provider
    Backward compatible với existing code
    """
    provider_instance = get_llm_provider(provider)
    return provider_instance.embed(prompt, model)


def chat(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    stream: bool = False,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    provider: Optional[str] = None
) -> Union[Dict, Iterator[Dict]]:
    """
    Chat with LLM using default or specified provider
    Backward compatible với existing code
    """
    provider_instance = get_llm_provider(provider)
    return provider_instance.chat(
        messages=messages,
        model=model,
        stream=stream,
        temperature=temperature,
        max_tokens=max_tokens
    )

