"""
Recursive Chunking Service
Tương đương với app/Services/RecursiveChunkingService.php trong Laravel

Chunking text thành các phần nhỏ hơn với overlap để giữ context
"""

from typing import List, Dict


class RecursiveChunkingService:
    """
    Service để chunk text thành các phần nhỏ hơn
    Tương đương với RecursiveChunkingService trong Laravel
    """
    
    def chunk(
        self, 
        text: str, 
        chunk_size: int = 1500, 
        overlap: int = 200
    ) -> List[Dict[str, any]]:
        """
        Split text thành semantic chunks với recursive approach và overlap
        
        Args:
            text: Text cần chunk
            chunk_size: Target size của mỗi chunk (characters)
            overlap: Số characters overlap giữa các chunks
            
        Returns:
            List of chunks, mỗi chunk có 'content' và 'metadata'
        """
        text = text.strip()
        
        # Đảm bảo overlap hợp lý (không quá 50% chunk size)
        overlap = min(overlap, int(chunk_size * 0.5))
        
        if len(text) <= chunk_size:
            return [self._create_chunk(text)]
        
        # Define splitters từ lớn đến nhỏ (semantic units)
        splitters = ["\n\n", "\n", ". ", " "]
        
        for splitter in splitters:
            parts = text.split(splitter)
            if len(parts) > 1:
                # Nếu split thành công, recursively process
                return self._recursively_process_parts(parts, splitter, chunk_size, overlap)
        
        # Nếu không có splitter nào work, split by character length với overlap
        return self._split_with_overlap(text, chunk_size, overlap)
    
    def _recursively_process_parts(
        self, 
        parts: List[str], 
        separator: str, 
        chunk_size: int, 
        overlap: int
    ) -> List[Dict[str, any]]:
        """
        Recursively process parts với overlap
        """
        chunks = []
        current_chunk = ""
        previous_chunk_end = ""  # Store end của previous chunk cho overlap
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Nếu một part vẫn quá lớn, recursively chunk nó
            if len(part) > chunk_size:
                # Nếu có overlap từ previous chunk, prepend nó vào part trước khi chunk
                part_to_chunk = (previous_chunk_end + separator if previous_chunk_end else "") + part
                sub_chunks = self.chunk(part_to_chunk, chunk_size, overlap)
                
                if sub_chunks:
                    # Add tất cả sub-chunks
                    chunks.extend(sub_chunks)
                    # Update previous_chunk_end từ last sub-chunk
                    last_sub_chunk = sub_chunks[-1]
                    previous_chunk_end = last_sub_chunk['content'][-overlap:] if len(last_sub_chunk['content']) > overlap else ""
                continue
            
            # Tính toán nếu thêm part này có vượt quá chunk size không
            potential_chunk = current_chunk + (separator if current_chunk else "") + part
            
            if len(potential_chunk) > chunk_size:
                if current_chunk:
                    # Save current chunk
                    chunks.append(self._create_chunk(current_chunk))
                    # Store end cho overlap
                    previous_chunk_end = current_chunk[-overlap:] if len(current_chunk) > overlap else ""
                # Start new chunk với overlap từ previous nếu có
                current_chunk = (previous_chunk_end + separator if previous_chunk_end else "") + part
            else:
                current_chunk = potential_chunk
        
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk))
        
        return chunks
    
    def _split_with_overlap(
        self, 
        text: str, 
        chunk_size: int, 
        overlap: int
    ) -> List[Dict[str, any]]:
        """
        Split text by character length với overlap (fallback method)
        """
        chunks = []
        length = len(text)
        start = 0
        previous_end = ""
        
        while start < length:
            # Calculate chunk end position
            chunk_end = min(start + chunk_size, length)
            
            # Extract chunk
            chunk_content = text[start:chunk_end]
            
            # Add overlap từ previous chunk nếu có
            if previous_end and start > 0:
                chunk_content = previous_end + chunk_content
            
            chunks.append(self._create_chunk(chunk_content))
            
            # Store end của current chunk cho next overlap
            previous_end = chunk_content[-overlap:] if len(chunk_content) > overlap else ""
            
            # Move start position (accounting for overlap)
            start = chunk_end - overlap
            
            # Prevent infinite loop
            if start <= 0 or start >= length:
                break
        
        return chunks
    
    def _create_chunk(self, content: str) -> Dict[str, any]:
        """
        Tạo chunk structure
        """
        return {
            'content': content,
            'metadata': {
                'length': len(content),
            },
        }

