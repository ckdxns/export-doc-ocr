"""
문서별 데이터 파서 및 정규화 엔진 (Parser & Field Normalizer)
"""
import re
from typing import Dict, Any, List, Optional
from config import (
    DOC_TYPE_PERFORMANCE,
    DOC_TYPE_DECLARATION,
    DOC_TYPE_UNKNOWN,
    COUNTRY_MAP
)

class DocumentParser:
    """
    추출된 텍스트에서 [나라, 기업, 성과월, 수출액]을 추출 및 정규화하는 파서.
    """

    def __init__(self):
        self.country_map = COUNTRY_MAP

    def normalize_country(self, raw_country: str) -> str:
        """
        국가명 또는 국가 코드를 한글 표준 국가명으로 정규화합니다.
        """
        if not raw_country:
            return "기타"
        
        # 괄호 및 불필요한 설명어구 제거
        cleaned = re.sub(r"\(.*?\)", "", raw_country).strip().upper()
        
        # 1. 영문 코드/이름 직접 매핑
        if cleaned in self.country_map:
            return self.country_map[cleaned]
            
        # 2. 한글 국가명 확인
        for code, kr_name in self.country_map.items():
            if kr_name in raw_country or code == cleaned:
                return kr_name
                
        # 3. 추가 공통 정제
        pure_hangul = re.sub(r"[^가-힣]", "", raw_country)
        if pure_hangul and pure_hangul not in ["국가명", "목적국", "수출국가", "상대국"]:
            return pure_hangul

        return "미확인국가"

    def normalize_month(self, raw_date: str) -> str:
        """
        다양한 날짜 형식을 'YYYY-MM' 형식으로 표준화합니다.
        예: '2024-01-15', '2024.02.20', '2024년 01월', '202401' -> '2024-01'
        """
        if not raw_date:
            return "2024-01"
            
        clean = raw_date.strip()
        
        # 1. YYYY-MM or YYYY.MM or YYYY/MM or YYYY년 MM월
        m = re.search(r"\b(20\d{2})[-./년\s]+(0[1-9]|1[0-2]|\d{1,2})\b", clean)
        if m:
            year = m.group(1)
            month = m.group(2).zfill(2)
            return f"{year}-{month}"
            
        # 2. 6자리 연속 숫자 (202401)
        m2 = re.search(r"\b(20\d{2})(0[1-9]|1[0-2])\b", clean)
        if m2:
            return f"{m2.group(1)}-{m2.group(2)}"
            
        return clean[:7] if len(clean) >= 7 else clean

    def normalize_amount(self, raw_amount: Any) -> float:
        """
        문자열에서 유효한 금액 숫자(콤마 포함, 소수점 포함)를 추출하여 실수(float)로 변환합니다.
        """
        if isinstance(raw_amount, (int, float)):
            return float(raw_amount)
        if not raw_amount:
            return 0.0
            
        text = str(raw_amount).strip()
        # 통화 단위 및 텍스트 제거하고 금액 패턴 추출
        numbers = re.findall(r"[\d,]+(?:\.\d+)?", text)
        if not numbers:
            return 0.0
            
        # 뒤에서부터 유효한 금액 탐색
        for num_str in reversed(numbers):
            try:
                cleaned_num = num_str.replace(",", "")
                val = float(cleaned_num)
                # 연도나 일자 등(2024 등)과 혼동되지 않도록 유효성 확인
                if val > 0:
                    return val
            except ValueError:
                continue
                
        return 0.0

    def parse_performance_certificate(self, text: str) -> Dict[str, Any]:
        """
        [수출실적증명서] 전용 파싱 로직
        """
        result = {
            "doc_type": DOC_TYPE_PERFORMANCE,
            "company": "",
            "country": "",
            "month": "",
            "amount": 0.0,
            "raw_fields": {}
        }

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        for line in lines:
            # 1. 상호 / 업체명
            if not result["company"] and any(k in line for k in ["상호", "업체명", "신청인", "수출자"]) and ":" in line:
                val = line.split(":", 1)[1].strip()
                if val and not any(header in val for header in ["정보", "현황", "내역"]):
                    result["company"] = val
                    result["raw_fields"]["company"] = line

            # 2. 국가 / 목적국
            if not result["country"] and any(k in line for k in ["수출국가", "목적국", "바이어국가", "상대국"]) and ":" in line:
                val = line.split(":", 1)[1].strip()
                result["country"] = self.normalize_country(val)
                result["raw_fields"]["country"] = line

            # 3. 실적연월 / 성과월
            if not result["month"] and any(k in line for k in ["실적연월", "실적기간", "성과월", "성과연월", "기간"]) and ":" in line:
                val = line.split(":", 1)[1].strip()
                result["month"] = self.normalize_month(val)
                result["raw_fields"]["month"] = line

            # 4. 수출금액 / 인정실적
            if result["amount"] == 0.0 and any(k in line for k in ["수출인정실적", "실적금액", "수출금액", "인정실적", "합계금액", "성약금액"]) and ":" in line:
                val = line.split(":", 1)[1].strip()
                result["amount"] = self.normalize_amount(val)
                result["raw_fields"]["amount"] = line

        # 2차 보완: 정규식 검색
        if not result["company"]:
            m_comp = re.search(r"(\((?:주|유)\)[가-힣A-Za-z0-9]+|[가-힣A-Za-z0-9]+\s*주식회사)", text)
            if m_comp:
                result["company"] = m_comp.group(1).strip()

        if not result["country"]:
            for k, v in self.country_map.items():
                if v in text or f" {k} " in text.upper():
                    result["country"] = v
                    break

        if not result["month"]:
            m_date = re.search(r"(?:발급일자|일자)\s*[:：]?\s*(\d{4}[-./년\s]+\d{1,2})", text)
            if m_date:
                result["month"] = self.normalize_month(m_date.group(1))

        if result["amount"] == 0.0:
            m_amt = re.search(r"(?:USD|\$|금액)\s*[:：]?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
            if m_amt:
                result["amount"] = self.normalize_amount(m_amt.group(1))

        return result

    def parse_export_declaration(self, text: str) -> Dict[str, Any]:
        """
        [수출신고필증] 전용 파싱 로직
        """
        result = {
            "doc_type": DOC_TYPE_DECLARATION,
            "company": "",
            "country": "",
            "month": "",
            "amount": 0.0,
            "raw_fields": {}
        }

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        for line in lines:
            # 1. 상호 / 수출화주: (5) 수출화주(상호) : (주)ABC
            if not result["company"] and ("(5)" in line or "수출화주" in line or "상호" in line) and ":" in line:
                val = line.split(":", 1)[1].strip()
                if val and not any(header in val for header in ["정보", "현황"]):
                    result["company"] = val
                    result["raw_fields"]["company"] = line

            # 2. 목적국: (11) 목적국(국가명) : 베트남 (VN)
            if not result["country"] and ("(11)" in line or "목적국" in line) and ":" in line:
                val = line.split(":", 1)[1].strip()
                result["country"] = self.normalize_country(val)
                result["raw_fields"]["country"] = line

            # 3. 신고수리일자: (52) 신고수리일자 : 2024-02-12
            if not result["month"] and ("(52)" in line or "신고수리일자" in line or "수리일자" in line) and ":" in line:
                val = line.split(":", 1)[1].strip()
                result["month"] = self.normalize_month(val)
                result["raw_fields"]["month"] = line

            # 4. 결제금액 / FOB금액: (48) 결제금액 : USD 30,000.00
            if result["amount"] == 0.0 and ("(48)" in line or "결제금액" in line or "총신고가격" in line or "FOB" in line) and ":" in line:
                val = line.split(":", 1)[1].strip()
                result["amount"] = self.normalize_amount(val)
                result["raw_fields"]["amount"] = line

        # 2차 보완: 정규식 검색
        if not result["company"]:
            m_comp = re.search(r"(?:\(5\)\s*(?:수출화주|상호)\s*[:：]?\s*|상호\(성명\)\s*[:：]?\s*)([가-힣A-Za-z0-9()（）주식회사\s]{2,30})", text)
            if m_comp:
                result["company"] = m_comp.group(1).strip()
            else:
                m_sub = re.search(r"(\((?:주|유)\)[가-힣A-Za-z0-9]+|[가-힣A-Za-z0-9]+\s*주식회사)", text)
                if m_sub:
                    result["company"] = m_sub.group(1).strip()

        if not result["country"]:
            m_cnt = re.search(r"(?:\(11\)\s*목적국(?:[가-힣\s()]*)\s*[:：]?\s*)([가-힣A-Za-z\s()]+)", text)
            if m_cnt:
                result["country"] = self.normalize_country(m_cnt.group(1))
            else:
                for k, v in self.country_map.items():
                    if v in text or f" {k} " in text.upper():
                        result["country"] = v
                        break

        if not result["month"]:
            m_date = re.search(r"(?:\(52\)\s*신고수리일자|신고수리일자|수리일자)\s*[:：]?\s*(\d{4}[-./년\s]+\d{1,2}(?:[-./일\s]+\d{1,2})?)", text)
            if m_date:
                result["month"] = self.normalize_month(m_date.group(1))

        if result["amount"] == 0.0:
            m_amt = re.search(r"(?:\(48\)\s*결제금액|결제금액|총신고가격)\s*[:：]?\s*(?:USD|KRW|\$)?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
            if m_amt:
                result["amount"] = self.normalize_amount(m_amt.group(1))

        return result

    def parse(self, text: str, doc_type: str) -> Dict[str, Any]:
        """
        문서 유형에 맞춰 파싱하고, 기본값을 안전하게 채웁니다.
        """
        if doc_type == DOC_TYPE_PERFORMANCE:
            parsed = self.parse_performance_certificate(text)
        elif doc_type == DOC_TYPE_DECLARATION:
            parsed = self.parse_export_declaration(text)
        else:
            parsed = self.parse_export_declaration(text)
            alt = self.parse_performance_certificate(text)
            for k in ["company", "country", "month", "amount"]:
                if not parsed.get(k) and alt.get(k):
                    parsed[k] = alt[k]

        # 기본값 및 정제
        if not parsed.get("company"):
            parsed["company"] = "(주)미상기업"
        if not parsed.get("country"):
            parsed["country"] = "기타"
        if not parsed.get("month"):
            parsed["month"] = "2024-01"
            
        return parsed
