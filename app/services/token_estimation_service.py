"""
Token Estimation Service
Tương đương với app/Services/TokenEstimationService.php trong Laravel

Estimate số tokens trong text để quản lý context window
"""


class TokenEstimationService:
    """
    Service để estimate tokens cho text
    Tương đương với TokenEstimationService trong Laravel
    
    Laravel sử dụng heuristic: ~4 characters per token
    Python version cũng dùng heuristic tương tự
    """
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate số tokens trong text
        Tương đương với estimateTokens() trong Laravel
        
        Args:
            text: Text cần estimate
            
        Returns:
            Estimated token count
        """
        if not text or not text.strip():
            return 0
        
        # Simple estimation: ~4 characters per token for English
        # This is a conservative estimate (actual may be 3-5 chars per token)
        # Tương đương với Laravel: ceil(mb_strlen($text) / 4)
        char_count = len(text)
        return (char_count + 3) // 4  # Ceiling division
    
    def estimate_tokens_for(self, texts):
        """
        Estimate tokens cho multiple texts
        Tương đương với estimateTokensFor() trong Laravel
        
        Args:
            texts: Single text (str) or array of texts (list)
            
        Returns:
            int nếu single text, list nếu multiple texts
        """
        if isinstance(texts, list):
            return [self.estimate_tokens(text) for text in texts]
        return self.estimate_tokens(texts)
    
    def would_exceed_limit(self, current_tokens: int, text_to_add: str, max_tokens: int) -> bool:
        """
        Check nếu adding text would exceed token limit
        Tương đương với wouldExceedLimit() trong Laravel
        
        Args:
            current_tokens: Current token count
            text_to_add: Text to potentially add
            max_tokens: Maximum allowed tokens
            
        Returns:
            True nếu adding would exceed limit
        """
        additional_tokens = self.estimate_tokens(text_to_add)
        return (current_tokens + additional_tokens) > max_tokens

