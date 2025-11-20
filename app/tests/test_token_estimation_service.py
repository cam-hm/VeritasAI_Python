"""
Tests for TokenEstimationService
"""

import pytest
from app.services.token_estimation_service import TokenEstimationService


@pytest.mark.unit
@pytest.mark.services
class TestTokenEstimationService:
    """Test TokenEstimationService"""
    
    def test_initialization(self):
        """Test service initialization"""
        service = TokenEstimationService()
        assert service is not None
    
    def test_estimate_tokens_short_text(self):
        """Test token estimation for short text"""
        service = TokenEstimationService()
        text = "Hello world"
        tokens = service.estimate_tokens(text)
        
        assert isinstance(tokens, int)
        assert tokens > 0
        assert tokens >= 2  # At least 2 words
    
    def test_estimate_tokens_long_text(self):
        """Test token estimation for long text"""
        service = TokenEstimationService()
        text = " ".join([f"word{i}" for i in range(100)])
        tokens = service.estimate_tokens(text)
        
        assert isinstance(tokens, int)
        assert tokens > 50  # Should be more than 50 tokens
    
    def test_estimate_tokens_empty(self):
        """Test token estimation for empty text"""
        service = TokenEstimationService()
        tokens = service.estimate_tokens("")
        
        assert tokens == 0
    
    def test_estimate_tokens_whitespace(self):
        """Test token estimation for whitespace-only text"""
        service = TokenEstimationService()
        tokens = service.estimate_tokens("   \n\t   ")
        
        # Should handle whitespace gracefully
        assert isinstance(tokens, int)
        assert tokens >= 0
    
    def test_estimate_tokens_special_characters(self):
        """Test token estimation with special characters"""
        service = TokenEstimationService()
        text = "Hello! @#$%^&*() world?"
        tokens = service.estimate_tokens(text)
        
        assert isinstance(tokens, int)
        assert tokens > 0
    
    def test_estimate_tokens_unicode(self):
        """Test token estimation with unicode characters"""
        service = TokenEstimationService()
        text = "Hello 世界 🌍"
        tokens = service.estimate_tokens(text)
        
        assert isinstance(tokens, int)
        assert tokens > 0

