"""
LLM Provider Abstraction Layer
Tương đương với Strategy Pattern trong OOP

Cho phép dễ dàng switch giữa các LLM providers:
- Ollama (local)
- OpenAI
- Anthropic (Claude)
- DeepSeek
- Together AI
- Groq
- etc.

Sử dụng LiteLLM để support 100+ providers với unified interface
"""

from .base import LLMProvider, LLMProviderFactory
from .litellm_provider import LiteLLMProvider

# Register providers using LiteLLM
# LiteLLM supports: openai, anthropic, deepseek, together, groq, ollama, etc.
LLMProviderFactory.register('ollama', LiteLLMProvider)
LLMProviderFactory.register('openai', LiteLLMProvider)
LLMProviderFactory.register('deepseek', LiteLLMProvider)
LLMProviderFactory.register('anthropic', LiteLLMProvider)
LLMProviderFactory.register('together', LiteLLMProvider)
LLMProviderFactory.register('groq', LiteLLMProvider)

__all__ = [
    'LLMProvider',
    'LLMProviderFactory',
    'LiteLLMProvider',
]

