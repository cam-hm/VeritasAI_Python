"""
Ollama Client
Tương đương với Camh\\Ollama\\Facades\\Ollama trong Laravel

Package tự viết để tương tác với Ollama API
Giống như Laravel package camh/laravel-ollama
"""

import httpx
import json
from typing import List, Dict, Optional, Iterator
import logging
from django.conf import settings as django_settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Ollama Client - tương đương với Ollama Facade trong Laravel
    
    Trong Laravel:
    - Camh\\Ollama\\Facades\\Ollama
    - Methods: embed(), chat(), generate(), etc.
    
    Trong Python:
    - OllamaClient class
    - Methods: embed(), chat(), generate(), etc.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        default_model: Optional[str] = None,
        embed_model: Optional[str] = None
    ):
        """
        Initialize Ollama client
        
        Args:
            base_url: Ollama base URL (default from settings)
            timeout: Request timeout in seconds
            default_model: Default model for chat/generate
            embed_model: Default model for embeddings
        """
        # Lazy load settings để tránh Django setup issues
        try:
            from django.conf import settings as django_settings
            self.base_url = base_url or getattr(
                django_settings, 
                'OLLAMA_BASE_URL', 
                'http://127.0.0.1:11434'
            )
            self.timeout = timeout or getattr(django_settings, 'OLLAMA_TIMEOUT', 60.0)
            self.default_model = default_model or getattr(
                django_settings, 
                'OLLAMA_CHAT_MODEL', 
                'llama3.1'
            )
            self.embed_model = embed_model or getattr(
                django_settings, 
                'OLLAMA_EMBED_MODEL', 
                'nomic-embed-text'
            )
        except Exception:
            # Fallback nếu Django chưa setup
            self.base_url = base_url or 'http://127.0.0.1:11434'
            self.timeout = timeout or 60.0
            self.default_model = default_model or 'llama3.1'
            self.embed_model = embed_model or 'nomic-embed-text'
    
    def embed(self, prompt: str | List[str], model: Optional[str] = None) -> List[float] | List[List[float]]:
        """
        Generate embedding(s) từ Ollama
        Tương đương với Ollama::embed($prompt) trong Laravel
        
        Args:
            prompt: Single prompt string hoặc list of prompts
            model: Model name (optional, uses default embed_model)
            
        Returns:
            Single embedding (list of floats) nếu prompt là string
            List of embeddings nếu prompt là list
        """
        model = model or self.embed_model
        url = f"{self.base_url}/api/embeddings"
        
        # Handle single prompt
        if isinstance(prompt, str):
            payload = {
                "model": model,
                "prompt": prompt,
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                if "embedding" in data and isinstance(data["embedding"], list):
                    return data["embedding"]
                else:
                    raise ValueError(f"Invalid embedding response structure: {data}")
        
        # Handle list of prompts (batch)
        else:
            # Ollama doesn't support batch embeddings natively
            # Process sequentially (có thể optimize sau)
            embeddings = []
            for p in prompt:
                embeddings.append(self.embed(p, model))
            return embeddings
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        stream: bool = False
    ) -> Dict | Iterator[Dict]:
        """
        Chat với Ollama
        Tương đương với Ollama::chat($messages) trong Laravel
        
        Args:
            messages: List of message dicts [{'role': 'user', 'content': '...'}, ...]
            model: Model name (optional, uses default_model)
            stream: Whether to stream response
            
        Returns:
            Dict với 'message' key nếu stream=False
            Iterator of dicts nếu stream=True
        """
        model = model or self.default_model
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        if stream:
            # Return streaming iterator
            return self._chat_stream(url, payload)
        else:
            # Return single response
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
    
    def _chat_stream(self, url: str, payload: Dict) -> Iterator[Dict]:
        """
        Internal method để handle streaming chat
        """
        with httpx.stream('POST', url, json=payload, timeout=self.timeout) as response:
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        yield data
                    except json.JSONDecodeError:
                        continue
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False
    ) -> Dict | Iterator[Dict]:
        """
        Generate text từ prompt
        Tương đương với Ollama::generate($prompt) trong Laravel
        
        Args:
            prompt: Text prompt
            model: Model name (optional)
            stream: Whether to stream response
            
        Returns:
            Dict với 'response' key nếu stream=False
            Iterator of dicts nếu stream=True
        """
        model = model or self.default_model
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }
        
        if stream:
            return self._generate_stream(url, payload)
        else:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
    
    def _generate_stream(self, url: str, payload: Dict) -> Iterator[Dict]:
        """
        Internal method để handle streaming generate
        """
        with httpx.stream('POST', url, json=payload, timeout=self.timeout) as response:
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        yield data
                    except json.JSONDecodeError:
                        continue
    
    def list_models(self) -> List[Dict]:
        """
        List available models
        Tương đương với Ollama::list() trong Laravel (nếu có)
        
        Returns:
            List of model dicts
        """
        url = f"{self.base_url}/api/tags"
        
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get('models', [])


# Tạo singleton instance (tương đương với Facade trong Laravel)
_ollama_client_instance = None

def get_ollama_client() -> OllamaClient:
    """
    Get Ollama client instance (singleton pattern)
    Tương đương với Ollama:: trong Laravel
    
    Usage:
        from app.services.ollama_client import get_ollama_client
        
        ollama = get_ollama_client()
        embedding = ollama.embed("text")
        response = ollama.chat([{'role': 'user', 'content': 'Hello'}])
    """
    global _ollama_client_instance
    if _ollama_client_instance is None:
        _ollama_client_instance = OllamaClient()
    return _ollama_client_instance


# Convenience functions (tương đương với static methods trong Laravel)
def embed(prompt: str | List[str], model: Optional[str] = None) -> List[float] | List[List[float]]:
    """
    Convenience function - tương đương với Ollama::embed() trong Laravel
    
    Usage:
        from app.services.ollama_client import embed
        
        embedding = embed("text")
        embeddings = embed(["text1", "text2"])
    """
    return get_ollama_client().embed(prompt, model)


def chat(
    messages: List[Dict[str, str]], 
    model: Optional[str] = None,
    stream: bool = False
) -> Dict | Iterator[Dict]:
    """
    Convenience function - tương đương với Ollama::chat() trong Laravel
    
    Usage:
        from app.services.ollama_client import chat
        
        response = chat([{'role': 'user', 'content': 'Hello'}])
    """
    return get_ollama_client().chat(messages, model, stream)

