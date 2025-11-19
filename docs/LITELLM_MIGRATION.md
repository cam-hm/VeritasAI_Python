# LiteLLM Migration Guide

## ✅ Đã hoàn thành

### 1. Cài đặt LiteLLM
- ✅ Added `litellm==1.52.0` vào `requirements.txt`
- ✅ Installed và tested

### 2. Refactor Providers
- ✅ Tạo `LiteLLMProvider` - unified provider cho tất cả LLM providers
- ✅ Register các providers: ollama, openai, deepseek, anthropic, together, groq
- ✅ Update `LLMProviderFactory` để support LiteLLMProvider
- ✅ Update `llm_service.py` để sử dụng LiteLLMProvider

### 3. Code Updates
- ✅ Update `views.py` để parse responses từ LiteLLM (normalized format)
- ✅ Backward compatible với existing code

## 📋 Supported Providers

LiteLLM hỗ trợ 100+ providers, bao gồm:

### Chat Models
- ✅ **Ollama** (local) - `ollama/llama3.1`
- ✅ **OpenAI** - `gpt-4`, `gpt-3.5-turbo`
- ✅ **DeepSeek** - `deepseek-chat`, `deepseek-coder`
- ✅ **Anthropic** - `claude-3-5-sonnet-20241022`
- ✅ **Together AI** - `meta-llama/Llama-2-70b-chat-hf`
- ✅ **Groq** - `llama-3.1-70b-versatile`

### Embedding Models
- ✅ **Ollama** - `ollama/nomic-embed-text`
- ✅ **OpenAI** - `text-embedding-3-small`, `text-embedding-3-large`

## 🔧 Configuration

### Settings (veritasai_django/settings.py)

```python
# Default provider
DEFAULT_LLM_PROVIDER = 'ollama'

# API Keys (optional - only if using that provider)
OPENAI_API_KEY = 'sk-...'
DEEPSEEK_API_KEY = 'sk-...'
ANTHROPIC_API_KEY = 'sk-...'
TOGETHER_API_KEY = '...'
GROQ_API_KEY = '...'
```

### Usage trong Code

```python
from app.services.llm_service import get_provider_for_session

# Tự động dùng provider từ session
provider = get_provider_for_session(chat_session)
response = provider.chat(messages, model=session.model_name)
```

## 🎯 Benefits

1. **Unified Interface**: Tất cả providers dùng chung interface
2. **100+ Providers**: Support nhiều providers mà không cần viết code riêng
3. **Auto Retry**: LiteLLM tự động retry failed requests
4. **Cost Tracking**: Built-in cost tracking
5. **Fallback**: Có thể setup fallback providers
6. **Less Code**: Không cần maintain nhiều provider implementations

## 📝 Next Steps

1. Test với các providers khác (cần API keys)
2. Update embedding_service để dùng LiteLLMProvider
3. Add provider selection UI
4. Setup cost tracking

## ⚠️ Notes

- Ollama models: Format `ollama/model_name` (e.g., `ollama/llama3.1`)
- Other providers: LiteLLM auto-detects từ model name
- Streaming: LiteLLM normalizes responses, nhưng format có thể khác nhau
- Embeddings: Một số providers (DeepSeek, Anthropic) không support embeddings

