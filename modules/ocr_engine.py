"""
하이브리드 OCR 및 텍스트 추출 엔진 (PyMuPDF + EasyOCR)
"""
import io
import os
import cv2
import numpy as np
from PIL import Image
import pymupdf  # PyMuPDF
import easyocr
from typing import List, Dict, Any, Tuple, Union

class OCREngine:
    """
    디지털 PDF와 스캔 이미지(PDF/이미지 파일)를 처리하는 하이브리드 엔진.
    """
    _easyocr_reader = None

    @classmethod
    def get_reader(cls):
        if cls._easyocr_reader is None:
            # GPU 사용 가능 여부 체크 후 초기화
            cls._easyocr_reader = easyocr.Reader(['ko', 'en'], gpu=False)
        return cls._easyocr_reader

    @staticmethod
    def preprocess_image(image: Union[np.ndarray, Image.Image]) -> np.ndarray:
        """
        OCR 인식률을 높이기 위한 이미지 전처리 파이프라인.
        """
        if isinstance(image, Image.Image):
            img_np = np.array(image.convert('RGB'))
        else:
            img_np = image.copy()

        # RGB -> Gray
        if len(img_np.shape) == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np

        # 대비 개선 (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # 미세 노이즈 제거
        denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)

        return denoised

    def extract_from_pdf_bytes(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        PDF 바이트 스트림에서 텍스트 및 이미지 OCR을 수행합니다.
        """
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        full_text_list = []
        pages_data = []

        for page_idx, page in enumerate(doc):
            # 1. 텍스트 레이어 직접 추출 시도
            text = page.get_text("text")
            
            # 텍스트 레이어가 충분히 존재하는 경우 (디지털 PDF)
            if text and len(text.strip()) > 30:
                full_text_list.append(text)
                pages_data.append({
                    "page": page_idx + 1,
                    "method": "digital_text",
                    "text": text,
                    "image": None
                })
            else:
                # 텍스트가 없는 스캔본인 경우 고해상도로 렌더링 후 EasyOCR 실행
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                preprocessed = self.preprocess_image(img)
                
                reader = self.get_reader()
                ocr_results = reader.readtext(preprocessed)
                
                extracted_lines = [res[1] for res in ocr_results]
                page_text = "\n".join(extracted_lines)
                full_text_list.append(page_text)
                
                pages_data.append({
                    "page": page_idx + 1,
                    "method": "easyocr",
                    "text": page_text,
                    "ocr_details": ocr_results,
                    "image": img
                })

        doc.close()
        return {
            "full_text": "\n\n".join(full_text_list),
            "pages": pages_data
        }

    def extract_from_image_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        이미지 바이트 스트림에서 OCR을 수행합니다.
        """
        img = Image.open(io.BytesIO(image_bytes))
        preprocessed = self.preprocess_image(img)

        reader = self.get_reader()
        ocr_results = reader.readtext(preprocessed)

        extracted_lines = [res[1] for res in ocr_results]
        page_text = "\n".join(extracted_lines)

        return {
            "full_text": page_text,
            "pages": [{
                "page": 1,
                "method": "easyocr",
                "text": page_text,
                "ocr_details": ocr_results,
                "image": img
            }]
        }

    def process_file(self, file_name: str, file_bytes: bytes) -> Dict[str, Any]:
        """
        파일 확장자에 따라 적절한 추출 메서드를 호출합니다.
        """
        ext = os.path.splitext(file_name)[1].lower()
        if ext == ".pdf":
            result = self.extract_from_pdf_bytes(file_bytes)
        elif ext in [".png", ".jpg", ".jpeg"]:
            result = self.extract_from_image_bytes(file_bytes)
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {ext}")

        result["file_name"] = file_name
        return result
