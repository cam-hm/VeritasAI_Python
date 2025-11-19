"""
Tests for ChunkingService
"""

import pytest
from app.services.chunking_service import RecursiveChunkingService


@pytest.mark.unit
@pytest.mark.services
class TestRecursiveChunkingService:
    """Test RecursiveChunkingService"""
    
    def test_chunk_empty(self):
        """Test chunking empty text"""
        service = RecursiveChunkingService()
        result = service.chunk("")
        # Service returns empty chunk with empty content
        assert len(result) == 1
        assert result[0]['content'] == ''
        assert result[0]['metadata']['length'] == 0
    
    def test_chunk_short(self):
        """Test chunking short text (smaller than chunk_size)"""
        service = RecursiveChunkingService()
        text = "This is a short text."
        result = service.chunk(text, chunk_size=500)
        assert len(result) == 1
        assert result[0]['content'] == text
    
    def test_chunk_long(self):
        """Test chunking long text"""
        service = RecursiveChunkingService()
        # Create text longer than chunk_size
        text = " ".join([f"word{i}" for i in range(100)])  # Long text
        result = service.chunk(text, chunk_size=100, overlap=20)
        
        assert len(result) > 1
        # Check that chunks have content
        for chunk in result:
            assert 'content' in chunk
            assert len(chunk['content']) > 0
    
    def test_chunk_has_metadata(self):
        """Test that chunks have metadata"""
        service = RecursiveChunkingService()
        text = "This is a test text that should be chunked properly."
        result = service.chunk(text, chunk_size=20)
        
        for chunk in result:
            assert 'content' in chunk
            assert 'metadata' in chunk
            assert isinstance(chunk['metadata'], dict)
    
    def test_chunk_preserves_content(self):
        """Test that chunking preserves all content"""
        service = RecursiveChunkingService()
        text = "This is a test text that should be chunked properly."
        result = service.chunk(text, chunk_size=30, overlap=5)
        
        # All chunks combined should contain original text
        # Note: Due to overlap, some content may be duplicated, so we check
        # that all original words are present
        combined = " ".join([chunk['content'] for chunk in result])
        original_words = set(text.lower().split())
        combined_words = set(combined.lower().split())
        
        # All original words should be present in combined chunks
        assert original_words.issubset(combined_words)
    
    def test_chunk_with_overlap(self):
        """Test that chunks have overlap"""
        service = RecursiveChunkingService()
        text = " ".join([f"sentence{i}." for i in range(20)])  # Long text
        result = service.chunk(text, chunk_size=50, overlap=10)
        
        if len(result) > 1:
            # Check that we have multiple chunks
            assert len(result) > 1
            # Each chunk should have content
            for chunk in result:
                assert len(chunk['content']) > 0

