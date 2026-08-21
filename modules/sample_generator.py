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
    수출실적증명서 및 관세청 수출신고필증 서식과 동일한 구조의
    가상 표준 샘플 PDF 및 이미지 파일을 동적으로 생성합니다.
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
        company: str = "(주)한국글로벌",
        country: str = "미국",
        month: str = "2024-05",
        amount: int = 50000,
        cert_no: str = "KITA-2024-08912"
    ) -> bytes:
        """
        한국무역협회 스타일의 '수출실적증명서' PDF 생성
        """
        font_path = cls._get_font_path()
        doc = pymupdf.open()
        page = doc.new_page(width=595, height=842)  # A4

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
   - 사업자등록번호 : 100-80-00000
   - 대표자명 : 홍길동
   - 소재지 : 서울특별시 강남구 영동대로 513

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

   2024년 05월 20일

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
        company: str = "(주)한국글로벌",
        country: str = "중국",
        country_code: str = "CN PRC",
        month_full: str = "2024/06/10",
        month_norm: str = "2024-06",
        amount_usd: int = 30000,
        amount_krw: int = 39000000,
        decl_no: str = "10000-24-900000X"
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

① 신고자 : 관세사무소 김종선
⑤ 신고번호 : {decl_no}       ⑥ 세관과 : 020-09       ⑦ 신고일자 : {month_full}

------------------------------------------------------------
[수출대행자 및 화주 정보]
② 수출대행자 : {company}
   (통관고유부호) 한국글로벌-1-18-1-01-5
   수출화주 : {company}
   (주소) 서울특별시 강남구 테헤란로 152
   (대표자) 홍길동              (소재지) 06236
   (사업자등록번호) 100-80-00000

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
㊽ 결제금액 : FOB-USD-{amount_usd:,}.00

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
        표준 가상 서식 샘플 4종 생성
        """
        samples = [
            {
                "name": "수출신고필증_한국글로벌_중국_30000.pdf",
                "bytes": cls.generate_export_declaration_pdf(
                    company="(주)한국글로벌", country="중국", country_code="CN PRC",
                    month_full="2024/06/10", month_norm="2024-06", amount_usd=30000, amount_krw=39000000
                ),
                "expected": {"doc_type": "수출신고필증", "company": "(주)한국글로벌", "country": "중국", "month": "2024-06", "amount": 30000.0}
            },
            {
                "name": "수출실적증명서_한국글로벌_미국_50000.pdf",
                "bytes": cls.generate_performance_certificate_pdf(
                    company="(주)한국글로벌", country="미국", month="2024-05", amount=50000, cert_no="KITA-2024-001"
                ),
                "expected": {"doc_type": "수출실적증명서", "company": "(주)한국글로벌", "country": "미국", "month": "2024-05", "amount": 50000.0}
            },
            {
                "name": "수출신고필증_에이비씨_일본_20000.pdf",
                "bytes": cls.generate_export_declaration_pdf(
                    company="(주)에이비씨", country="일본", country_code="JP JAPAN",
                    month_full="2024/03/12", month_norm="2024-03", amount_usd=20000, amount_krw=26000000, decl_no="110-24-00883Y"
                ),
                "expected": {"doc_type": "수출신고필증", "company": "(주)에이비씨", "country": "일본", "month": "2024-03", "amount": 20000.0}
            },
            {
                "name": "수출실적증명서_글로벌테크_독일_75000.pdf",
                "bytes": cls.generate_performance_certificate_pdf(
                    company="(주)글로벌테크", country="독일", month="2024-04", amount=75000, cert_no="KITA-2024-099"
                ),
                "expected": {"doc_type": "수출실적증명서", "company": "(주)글로벌테크", "country": "독일", "month": "2024-04", "amount": 75000.0}
            }
        ]
        return samples
