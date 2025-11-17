"""
Text Extraction Service
Tương đương với app/Services/TextExtractionService.php trong Laravel

Trong Laravel:
- Sử dụng Spatie\PdfToText\Pdf cho PDF
- Sử dụng PhpOffice\PhpWord\IOFactory cho DOCX

Trong Python:
- Sử dụng PyPDF2 cho PDF
- Sử dụng python-docx cho DOCX
"""

import os
from pathlib import Path
from typing import Optional
import PyPDF2
from docx import Document as DocxDocument


class TextExtractionService:
    """
    Service để extract text từ các file types khác nhau
    Tương đương với TextExtractionService trong Laravel
    """
    
    def extract(self, file_path: str) -> str:
        """
        Extract text từ file
        
        Args:
            file_path: Đường dẫn đến file
            
        Returns:
            Text content của file
            
        Raises:
            ValueError: Nếu file type không được support
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Lấy extension (tương đương pathinfo($filePath, PATHINFO_EXTENSION) trong PHP)
        extension = Path(file_path).suffix.lower().lstrip('.')
        
        if extension == 'pdf':
            return self._extract_pdf(file_path)
        elif extension == 'docx':
            return self._extract_docx(file_path)
        elif extension in ['txt', 'md']:
            return self._extract_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
    
    def _extract_pdf(self, file_path: str) -> str:
        """
        Extract text từ PDF file
        Tương đương với Pdf::getText($filePath) trong Laravel
        """
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise RuntimeError(f"Error extracting PDF: {str(e)}")
        
        return text.strip()
    
    def _extract_docx(self, file_path: str) -> str:
        """
        Extract text từ DOCX file
        Tương đương với PhpWord processing trong Laravel
        """
        try:
            doc = DocxDocument(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + " "
            return text.strip()
        except Exception as e:
            raise RuntimeError(f"Error extracting DOCX: {str(e)}")
    
    def _extract_text(self, file_path: str) -> str:
        """
        Extract text từ plain text files (TXT, MD)
        Tương đương với file_get_contents($filePath) trong Laravel
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            raise RuntimeError(f"Error reading text file: {str(e)}")

