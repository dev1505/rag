from pypdf import PdfReader
from PIL import Image
import pytesseract
from docx import Document
import io

class Parsers:
    @staticmethod
    def pdf_parser(file_path: str) -> str:
        text_content = ""
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
        except Exception as e:
            raise RuntimeError(f"Failed to parse PDF: {e}")
        return text_content.strip()
    
    @staticmethod
    def image_parser(image_path: str) -> str:
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            raise RuntimeError(f"Failed to parse image: {e}")
        
    @staticmethod
    def word_parser(file_bytes: bytes) -> str:
        """Extract text from a .docx Word document"""
        doc = Document(io.BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
