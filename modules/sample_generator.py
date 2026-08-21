"""
테스트 및 시연용 샘플 문서 생성기 (PDF 및 이미지 생성)
관세청 유니패스(UNI-PASS) 수출신고필증 및 한국무역협회 수출실적증명서 표준 양식
"""
import os
import io
import pymupdf
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any

class SampleGenerator:
    """
    실제 수출실적증명서 및 관세청 수출신고필증 서식과 동일한 구조의
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
        company: str = "(주)라온코퍼레이션",
        country: str = "미국",
        month: str = "2025-04",
        amount: int = 50000,
        cert_no: str = "KITA-2025-08912"
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
   - 사업자등록번호 : 219-86-01252
   - 대표자명 : 김지연
   - 소재지 : 경기도 남양주시 다산지금로 202

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

   2025년 04월 20일

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
        company: str = "(주)라온코퍼레이션",
        country: str = "중국",
        country_code: str = "CN PRC",
        month_full: str = "2025/05/06",
        month_norm: str = "2025-05",
        amount_usd: int = 23202,
        amount_krw: int = 34283617,
        decl_no: str = "10996-25-900060X"
    ) -> bytes:
        """
        관세청 유니패스(UNI-PASS) 표준 양식 스타일의 '수출신고필증(적재전, 갑지)' PDF 생성
        """
        font_path = cls._get_font_path()
        doc = pymupdf.open()
        page = doc.new_page(width=595, height=842)

        page.draw_rect(pymupdf.Rect(40, 40, 555, 800), color=(0.2, 0.2, 0.2), width=1.5)

        text_content = f"""
============================================================
              수  출  신  고  필  증 (적재전, 갑지)
                     [ UNI-PASS 관세청 ]
============================================================

① 신고자 : 그린관세사무소 김종선
⑤ 신고번호 : {decl_no}       ⑥ 세관과 : 020-09       ⑦ 신고일자 : {month_full}

------------------------------------------------------------
[수출대행자 및 화주 정보]
② 수출대행자 : {company}
   (통관고유부호) 라온코퍼-1-18-1-01-5
   수출화주 : {company}
   (주소) 경기도 남양주시 다산지금로 202
   (대표자) 김지연              (소재지) 12284
   (사업자등록번호) 219-86-01252

------------------------------------------------------------
[거래 및 목적국 정보]
⑪ 거래구분 : 11 일반형태      ⑫ 종류 : A 일반수출
⑬ 목적국 : {country_code} (국가명: {country})
⑭ 적재항 : KRINC 인천항       ⑮ 선박회사 : (항공사)

------------------------------------------------------------
[결제 및 총신고가격 정보]
㉒ 결제방법 : TT 단순송금방식
㊺ 총신고가격(FOB) : 
    $ {amount_usd:,} (달러화)
    ₩ {amount_krw:,} (원화)
㊽ 결제금액 : FOB-KRW-34,283,617.00

------------------------------------------------------------
㊿ 신고수리일자 : {month_full}
담당자 : 관세청 인천세관장

============================================================
"""
        kwargs = {}
        if font_path:
            kwargs["fontfile"] = font_path
            kwargs["fontname"] = "malgun"

        page.insert_text(pymupdf.Point(60, 80), text_content, fontsize=10, **kwargs)

        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes

    @classmethod
    def generate_all_samples(cls) -> List[Dict[str, Any]]:
        """
        관세청 유니패스 및 무역협회 실전 서식 샘플 4종 생성
        """
        samples = [
            {
                "name": "수출신고필증_라온코퍼레이션_중국_23202.pdf",
                "bytes": cls.generate_export_declaration_pdf(
                    company="(주)라온코퍼레이션", country="중국", country_code="CN PRC",
                    month_full="2025/05/06", month_norm="2025-05", amount_usd=23202, amount_krw=34283617
                ),
                "expected": {"doc_type": "수출신고필증", "company": "(주)라온코퍼레이션", "country": "중국", "month": "2025-05", "amount": 23202.0}
            },
            {
                "name": "수출실적증명서_라온코퍼레이션_미국_50000.pdf",
                "bytes": cls.generate_performance_certificate_pdf(
                    company="(주)라온코퍼레이션", country="미국", month="2025-04", amount=50000, cert_no="KITA-2025-001"
                ),
                "expected": {"doc_type": "수출실적증명서", "company": "(주)라온코퍼레이션", "country": "미국", "month": "2025-04", "amount": 50000.0}
            },
            {
                "name": "수출신고필증_XYZ_일본_20000.pdf",
                "bytes": cls.generate_export_declaration_pdf(
                    company="(주)XYZ", country="일본", country_code="JP JAPAN",
                    month_full="2025/01/12", month_norm="2025-01", amount_usd=20000, amount_krw=26800000, decl_no="110-25-00883Y"
                ),
                "expected": {"doc_type": "수출신고필증", "company": "(주)XYZ", "country": "일본", "month": "2025-01", "amount": 20000.0}
            },
            {
                "name": "수출실적증명서_글로벌테크_독일_75000.pdf",
                "bytes": cls.generate_performance_certificate_pdf(
                    company="(주)글로벌테크", country="독일", month="2025-03", amount=75000, cert_no="KITA-2025-099"
                ),
                "expected": {"doc_type": "수출실적증명서", "company": "(주)글로벌테크", "country": "독일", "month": "2025-03", "amount": 75000.0}
            }
        ]
        return samples
