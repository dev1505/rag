from pypdf import PdfReader
from PIL import Image
import pytesseract
from docx import Document
import io


class Parsers:
    @staticmethod
    def pdf_parser_from_upload(pdf_bytes) -> str:
        text_content = ""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
        except Exception as e:
            raise RuntimeError(f"Failed to parse PDF: {e}")
        return text_content.strip()

    @staticmethod
    def image_parser_from_upload(image_bytes) -> str:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            raise RuntimeError(f"Failed to parse image: {e}")

    @staticmethod
    def word_parser_from_upload(file_bytes) -> str:
        try:
            file_bytes = file_bytes
            doc = Document(io.BytesIO(file_bytes))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise RuntimeError(f"Failed to parse Word document: {e}")
