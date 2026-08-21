"""
테스트 및 시연용 샘플 문서 생성기 (PDF 및 이미지 생성)
"""
import os
import io
import pymupdf
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any

class SampleGenerator:
    """
    실제 수출실적증명서 및 수출신고필증 서식과 동일한 구조의
    샘플 PDF 및 이미지 파일을 동적으로 생성합니다.
    """

    @staticmethod
    def _get_font_path():
        candidates = [
            "C:/Windows/Fonts/malgun.ttf",
            "C:/Windows/Fonts/gulim.ttc",
            "C:/Windows/Fonts/batang.ttc",
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return None

    @classmethod
    def generate_performance_certificate_pdf(
        cls,
        company: str = "(주)ABC",
        country: str = "미국",
        month: str = "2024-01",
        amount: int = 50000,
        cert_no: str = "KITA-2024-08912"
    ) -> bytes:
        """
        한국무역협회 스타일의 '수출실적증명서' PDF 생성
        """
        font_path = cls._get_font_path()
        doc = pymupdf.open()
        page = doc.new_page(width=595, height=842)  # A4

        # 테두리
        page.draw_rect(pymupdf.Rect(40, 40, 555, 800), color=(0.1, 0.2, 0.4), width=1.5)
        
        text_content = f"""
============================================================
                     수 출 실 적 증 명 서
============================================================

발급번호 : {cert_no}
발급기관 : 한국무역협회 (Korea International Trade Association)
발급일자 : {month}-15

1. 신청인(수출자) 정보
   - 상호(업체명) : {company}
   - 사업자등록번호 : 123-45-67890
   - 대표자명 : 홍길동
   - 소재지 : 서울특별시 강남구 영동대로 511

2. 수출 실적 내역
   ------------------------------------------------------------
   수출국가(목적국) : {country}
   실적연월(성과월) : {month}
   결제통화 : USD ($)
   수출인정실적(금액) : {amount:,} USD
   ------------------------------------------------------------

3. 용도 및 확인사항
   본 증명서는 대외무역법 시행령 제26조 규정에 의하여 상기 업체의
   수출실적(성약액)이 사실과 틀림없음을 증명합니다.

   2024년 01월 20일

                    한 국 무 역 협 회 장 (직인생략)
============================================================
"""
        kwargs = {}
        if font_path:
            kwargs["fontfile"] = font_path
            kwargs["fontname"] = "malgun"
            
        page.insert_text(pymupdf.Point(60, 80), text_content, fontsize=11, **kwargs)
        
        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes

    @classmethod
    def generate_export_declaration_pdf(
        cls,
        company: str = "(주)ABC",
        country: str = "베트남",
        month: str = "2024-02",
        amount: int = 30000,
        decl_no: str = "110-24-0102934X"
    ) -> bytes:
        """
        관세청 표준 양식 스타일의 '수출신고필증' PDF 생성
        """
        font_path = cls._get_font_path()
        doc = pymupdf.open()
        page = doc.new_page(width=595, height=842)

        page.draw_rect(pymupdf.Rect(40, 40, 555, 800), color=(0.2, 0.2, 0.2), width=1.5)

        text_content = f"""
============================================================
                    수  출  신  고  필  증
                [ EXPORT DECLARATION CERTIFICATE ]
============================================================

(1) 신고번호 : {decl_no}       (2) 세관/과 : 부산세관 통관국
(3) 신고일자 : {month}-10              (52) 신고수리일자 : {month}-12

------------------------------------------------------------
[수출자 및 화주 정보]
(4) 수출대행자 : 
(5) 수출화주(상호) : {company}
    - 사업자번호 : 220-81-99881
    - 소재지 : 경기도 성남시 분당구 판교역로 100

------------------------------------------------------------
[운송 및 거래조건]
(11) 목적국(국가명) : {country} (VN)
(12) 적재항 : KR PUS (부산항)
(13) 양륙항 : VN SGN (호치민)
(27) 인도조건 : FOB

------------------------------------------------------------
[결제 및 신고 금액]
(48) 결제금액 : USD {amount:,}.00
(49) 총신고가격(FOB) : USD {amount:,}.00
(50) 환율 : 1,320.50

------------------------------------------------------------
위 물품의 수출신고를 관세법 제248조의 규정에 의하여 수리합니다.

                          관  세  청  장
============================================================
"""
        kwargs = {}
        if font_path:
            kwargs["fontfile"] = font_path
            kwargs["fontname"] = "malgun"

        page.insert_text(pymupdf.Point(60, 80), text_content, fontsize=11, **kwargs)

        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes

    @classmethod
    def generate_all_samples(cls) -> List[Dict[str, Any]]:
        """
        기본 시연 및 테스트를 위한 4개의 표준 샘플 생성
        """
        samples = [
            {
                "name": "수출실적증명서_ABC_미국_50000.pdf",
                "bytes": cls.generate_performance_certificate_pdf(
                    company="(주)ABC", country="미국", month="2024-01", amount=50000, cert_no="KITA-2024-001"
                ),
                "expected": {"doc_type": "수출실적증명서", "company": "(주)ABC", "country": "미국", "month": "2024-01", "amount": 50000.0}
            },
            {
                "name": "수출신고필증_ABC_베트남_30000.pdf",
                "bytes": cls.generate_export_declaration_pdf(
                    company="(주)ABC", country="베트남", month="2024-02", amount=30000, decl_no="110-24-00192X"
                ),
                "expected": {"doc_type": "수출신고필증", "company": "(주)ABC", "country": "베트남", "month": "2024-02", "amount": 30000.0}
            },
            {
                "name": "수출신고필증_XYZ_일본_20000.pdf",
                "bytes": cls.generate_export_declaration_pdf(
                    company="(주)XYZ", country="일본", month="2024-01", amount=20000, decl_no="110-24-00883Y"
                ),
                "expected": {"doc_type": "수출신고필증", "company": "(주)XYZ", "country": "일본", "month": "2024-01", "amount": 20000.0}
            },
            {
                "name": "수출실적증명서_글로벌테크_독일_75000.pdf",
                "bytes": cls.generate_performance_certificate_pdf(
                    company="(주)글로벌테크", country="독일", month="2024-03", amount=75000, cert_no="KITA-2024-099"
                ),
                "expected": {"doc_type": "수출실적증명서", "company": "(주)글로벌테크", "country": "독일", "month": "2024-03", "amount": 75000.0}
            }
        ]
        return samples
