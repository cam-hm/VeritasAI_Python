# LLM Provider Architecture

## 🎯 Mục đích

Thiết kế abstraction layer để dễ dàng switch giữa các LLM providers mà không cần thay đổi business logic.

## 🏗️ Architecture

### Strategy Pattern + Factory Pattern

```
┌─────────────────────────────────────────────────────────┐
│                    Business Logic                        │
│              (views.py, services, etc.)                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Uses
                     ▼
┌─────────────────────────────────────────────────────────┐
│              LLMProviderFactory                          │
│         (Factory Pattern - creates providers)           │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Creates
                     ▼
┌─────────────────────────────────────────────────────────┐
│              LLMProvider (Abstract)                      │
│         (Strategy Pattern - interface)                  │
└──────┬──────────────┬──────────────┬────────────────────┘
       │              │              │
       ▼              ▼              ▼
┌──────────┐    ┌──────────┐   ┌──────────┐
│ Ollama   │    │ OpenAI   │   │ DeepSeek │
│ Provider │    │ Provider │   │ Provider │
└──────────┘    └──────────┘   └──────────┘
```

## 📁 File Structure

```
app/services/
├── llm_providers/
│   ├── __init__.py          # Register providers
│   ├── base.py              # LLMProvider abstract class + Factory
│   ├── ollama_provider.py   # Ollama implementation
│   ├── openai_provider.py   # OpenAI implementation
│   └── deepseek_provider.py # DeepSeek implementation
├── llm_service.py           # High-level service (convenience functions)
└── ollama_client.py         # Existing Ollama client (wrapped by OllamaProvider)
```

## 🔌 Supported Providers

### 1. Ollama (Local)
- **Provider Name**: `ollama`
- **Models**: llama3.1, mistral, etc.
- **Features**: Chat, Embeddings, Local deployment
- **Config**: `OLLAMA_BASE_URL`, `OLLAMA_CHAT_MODEL`, `OLLAMA_EMBED_MODEL`

### 2. OpenAI
- **Provider Name**: `openai`
- **Models**: gpt-4, gpt-3.5-turbo, text-embedding-3-small, etc.
- **Features**: Chat, Embeddings
- **Config**: `OPENAI_API_KEY`

### 3. DeepSeek
- **Provider Name**: `deepseek`
- **Models**: deepseek-chat, deepseek-coder
- **Features**: Chat (no embeddings)
- **Config**: `DEEPSEEK_API_KEY`

## 💻 Usage

### Basic Usage

```python
from app.services.llm_service import get_llm_provider

# Get default provider
provider = get_llm_provider()

# Get specific provider
provider = get_llm_provider('openai')

# Chat
response = provider.chat(
    messages=[{'role': 'user', 'content': 'Hello'}],
    model='gpt-3.5-turbo',
    stream=False
)

# Embeddings
embedding = provider.embed("text to embed")
```

### With ChatSession

```python
from app.services.llm_service import get_provider_for_session

# Get provider based on session.model_provider
provider = get_provider_for_session(chat_session)

# Use provider
response = provider.chat(messages, model=session.model_name)
```

### In Views

```python
# Old way (hardcoded Ollama)
from app.services.ollama_client import get_ollama_client
ollama = get_ollama_client()
response = ollama.chat(messages)

# New way (provider-agnostic)
from app.services.llm_service import get_provider_for_session
provider = get_provider_for_session(session)
response = provider.chat(messages, model=session.model_name)
```

## 🔧 Adding New Provider

### Step 1: Create Provider Class

```python
# app/services/llm_providers/anthropic_provider.py
from .base import LLMProvider

class AnthropicProvider(LLMProvider):
    @property
    def provider_name(self) -> str:
        return 'anthropic'
    
    def embed(self, prompt, model=None):
        # Implement embedding
        pass
    
    def chat(self, messages, model=None, stream=False, ...):
        # Implement chat
        pass
    
    def list_models(self):
        # Return available models
        pass
```

### Step 2: Register Provider

```python
# app/services/llm_providers/__init__.py
from .anthropic_provider import AnthropicProvider

LLMProviderFactory.register('anthropic', AnthropicProvider)
```

### Step 3: Update Model Choices

```python
# app/models.py
model_provider = models.CharField(
    choices=[
        ('ollama', 'Ollama'),
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),  # Add new
        ('deepseek', 'DeepSeek'),
    ]
)
```

## ⚙️ Configuration

### Settings

```python
# veritasai_django/settings.py

# Default provider
DEFAULT_LLM_PROVIDER = 'ollama'  # or 'openai', 'deepseek'

# Ollama
OLLAMA_BASE_URL = 'http://127.0.0.1:11434'
OLLAMA_CHAT_MODEL = 'llama3.1'
OLLAMA_EMBED_MODEL = 'nomic-embed-text'

# OpenAI
OPENAI_API_KEY = 'sk-...'

# DeepSeek
DEEPSEEK_API_KEY = 'sk-...'
```

## 🔄 Migration Path

### Current Code (Ollama-only)
```python
from app.services.ollama_client import get_ollama_client
ollama = get_ollama_client()
response = ollama.chat(messages)
```

### New Code (Provider-agnostic)
```python
from app.services.llm_service import get_llm_provider
provider = get_llm_provider('ollama')  # or 'openai', etc.
response = provider.chat(messages)
```

### Backward Compatibility
- `OllamaClient` vẫn hoạt động bình thường
- `OllamaProvider` wraps `OllamaClient`
- Existing code không bị break

## 📊 Benefits

1. **Flexibility**: Dễ dàng switch providers
2. **Testability**: Có thể mock providers trong tests
3. **Extensibility**: Dễ thêm providers mới
4. **User Choice**: Users có thể chọn provider per session
5. **Cost Optimization**: Có thể dùng Ollama (free) cho dev, OpenAI cho production

## 🎯 Future Enhancements

- [ ] Anthropic (Claude) provider
- [ ] Google Gemini provider
- [ ] Azure OpenAI provider
- [ ] Provider-specific features (function calling, etc.)
- [ ] Cost tracking per provider
- [ ] Automatic failover between providers

