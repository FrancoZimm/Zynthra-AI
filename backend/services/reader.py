"""Document parsers for various file formats.

Handles extraction of text content from PDF, DOCX, TXT, MD files.
"""
import logging
from pathlib import Path
from typing import Optional
import io

logger = logging.getLogger(__name__)


class DocumentReader:
    """Reads and extracts text from various document formats."""
    
    SUPPORTED_EXTENSIONS = {'.txt', '.md', '.pdf', '.docx', '.xlsx', '.xls'}
    
    @classmethod
    def is_supported(cls, filename: str) -> bool:
        """Check if file extension is supported."""
        ext = Path(filename).suffix.lower()
        return ext in cls.SUPPORTED_EXTENSIONS
    
    @classmethod
    def parse(cls, content: bytes, filename: str) -> Optional[str]:
        """Parse document content based on file extension.
        
        Args:
            content: Raw file bytes
            filename: Original filename (for extension detection)
            
        Returns:
            Extracted text content, or None if parsing failed
        """
        ext = Path(filename).suffix.lower()
        
        try:
            if ext in ('.txt', '.md'):
                return cls._parse_text(content)
            elif ext == '.pdf':
                return cls._parse_pdf(content)
            elif ext == '.docx':
                return cls._parse_docx(content)
            elif ext in ('.xlsx', '.xls'):
                return cls._parse_excel(content)
            else:
                logger.warning(f"Unsupported file type: {ext}")
                return None
        except Exception as e:
            logger.error(f"Failed to parse {filename}: {e}")
            return None
    
    @staticmethod
    def _parse_text(content: bytes) -> str:
        """Parse plain text (TXT, MD)."""
        for encoding in ('utf-8', 'latin-1', 'cp1252'):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return content.decode('utf-8', errors='replace')
    
    @staticmethod
    def _parse_pdf(content: bytes) -> str:
        """Parse PDF using pypdf."""
        try:
            from pypdf import PdfReader
        except ImportError:
            logger.error("pypdf not installed. Run: pip install pypdf")
            return ""
        
        reader = PdfReader(io.BytesIO(content))
        text_parts = []
        
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                if text and text.strip():
                    text_parts.append(f"[Página {i + 1}]\n{text}")
            except Exception as e:
                logger.warning(f"Failed to extract page {i + 1}: {e}")
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    def _parse_docx(content: bytes) -> str:
        """Parse DOCX using python-docx."""
        try:
            from docx import Document
        except ImportError:
            logger.error("python-docx not installed. Run: pip install python-docx")
            return ""
        
        doc = Document(io.BytesIO(content))
        text_parts = []
        
        # Extract paragraphs
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        
        # Extract table contents
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(
                    cell.text.strip() for cell in row.cells if cell.text.strip()
                )
                if row_text:
                    text_parts.append(row_text)
        
        return "\n".join(text_parts)
    
    @staticmethod
    def _parse_excel(content: bytes) -> str:
        """Parse Excel (XLSX/XLS) using openpyxl."""
        try:
            from openpyxl import load_workbook
        except ImportError:
            logger.error("openpyxl not installed. Run: pip install openpyxl")
            return ""
        
        wb = load_workbook(io.BytesIO(content), data_only=True)
        text_parts = []
        
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            text_parts.append(f"[Hoja: {sheet_name}]")
            
            for row in ws.iter_rows(values_only=True):
                # Skip empty rows
                if not any(cell is not None and str(cell).strip() for cell in row):
                    continue
                row_text = " | ".join(
                    str(cell).strip() if cell is not None else "" 
                    for cell in row
                )
                text_parts.append(row_text)
            
            text_parts.append("")  # Blank line between sheets
        
        return "\n".join(text_parts)
