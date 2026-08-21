"""
문서별 데이터 파서 및 정규화 엔진 (Parser & Field Normalizer)
관세청 유니패스(UNI-PASS) 수출신고필증 및 한국무역협회 수출실적증명서 표준 대응
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
    추출된 텍스트에서 [나라, 기업, 성과월, 수출액]을 추출 및 정규화하는 범용 파서.
    """

    def __init__(self):
        self.country_map = COUNTRY_MAP

    def clean_company_name(self, raw_name: str) -> str:
        """
        회사명에서 법인 형태를 보존하고 사업자등록번호, 대표자명, 주소, 표 헤더 등의 잡음을 제거합니다.
        """
        if not raw_name:
            return ""

        # 서식 안내/환급신청인/기타 비회사 문구 제외
        if any(k in raw_name for k in ["환급신청인", "1:수출", "2제조자", "제조미상", "제조자", "물품소재지", "사업자등록번호", "세관", "신고자"]):
            return ""

        # 1. '(주)기업명' or '(유)기업명'
        m_pref = re.search(r"(\((?:주|유|사|재|합|합자)\)\s*[가-힣A-Za-z0-9]+)", raw_name)
        if m_pref:
            return m_pref.group(1).replace(" ", "")

        # 2. '기업명(주)' or '기업명 주식회사'
        m_suff = re.search(r"([가-힣A-Za-z0-9]{2,}\s*(?:\((?:주|유)\)|주식회사|유한회사))", raw_name)
        if m_suff:
            return m_suff.group(1).replace(" ", "")

        # 3. 라벨 접두어 제거
        clean = re.sub(r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮㉒㊺㊽㊿0-9.()（）\s]*(?:수출대행자|수출화주|수출자|상호|기업명|발급대상자|업체명|신청인)\s*[:：]?", "", raw_name).strip()

        # 4. 뒤따라붙은 테이블 헤더 및 다른 컬럼 데이터 절단
        stop_words = [
            "통관고유부호", "수출자구분", "목적국", "적재항", "선박회사", "선박", "항공사", "PRC", "CN", "US", "USA",
            "인천항", "부산항", "출항예정일자", "적재예정보세구역", "주소", "대표자", "소재지", "사업자등록번호", "정보", "현황",
            "거래구분", "종류", "결제방법", "운송형태"
        ]
        for sw in stop_words:
            if sw in clean:
                clean = clean.split(sw)[0].strip()

        clean = re.sub(r"[()（）:;_\-/]+$", "", clean).strip()

        if len(clean) >= 2 and not any(h in clean for h in ["통관", "대표", "소재지", "정보", "신청", "환급"]):
            return clean

        return ""

    def normalize_country(self, raw_country: str) -> str:
        """
        (13) 목적국 영역의 ISO 국가코드 또는 영문/한글 국가명을 한글 정식 국가명으로 디코딩합니다.
        예: 'US' -> '미국', 'VN' -> '베트남', 'CN' -> '중국', 'JP' -> '일본'
        """
        if not raw_country:
            return ""

        # 라벨 제거
        clean_text = re.sub(r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮㉒㊺㊽㊿0-9.()（）\s]*(?:목적국|수출국가|수출국|바이어국가)\s*[:：]?", "", raw_country).strip()

        # 1. 단어 토큰별 매핑 검사
        tokens = re.split(r"[\s,()（）:;_\-/]+", clean_text.upper())
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            if token in self.country_map:
                return self.country_map[token]

        # 2. 문자열 내 등록된 국가명/코드 포함 여부 확인
        for code, kr in self.country_map.items():
            if kr in clean_text or f" {code} " in f" {clean_text.upper()} " or clean_text.upper() == code:
                return kr

        return ""

    def normalize_month(self, raw_date: str) -> str:
        """
        날짜 문자열에서 연월(YYYY-MM)을 추출합니다. (Format: YYYY-MM)
        예: '2024/05/10' -> '2024-05'
        """
        if not raw_date:
            return ""
            
        clean = raw_date.strip()
        
        # 1. YYYY/MM/DD or YYYY-MM-DD or YYYY.MM.DD
        m = re.search(r"\b(20\d{2})[-./년\s]+(0[1-9]|1[0-2]|\d{1,2})", clean)
        if m:
            year = m.group(1)
            month = m.group(2).zfill(2)
            return f"{year}-{month}"
            
        # 2. 8자리 또는 6자리 연속 숫자 (YYYYMMDD or YYYYMM)
        m2 = re.search(r"\b(20\d{2})(0[1-9]|1[0-2])(?:\d{2})?\b", clean)
        if m2:
            return f"{m2.group(1)}-{m2.group(2)}"
            
        return ""

    def normalize_amount(self, raw_amount: Any) -> float:
        """
        통화기호($, ₩, USD 등) 및 콤마(,)를 모두 제거하고 pure numeric(float) 금액을 추출합니다.
        달러(USD) 기준 금액을 우선 추출합니다.
        """
        if isinstance(raw_amount, (int, float)):
            return float(raw_amount)
        if not raw_amount:
            return 0.0
            
        text = str(raw_amount).strip()

        # 1. 달러 기호($) 직후 숫자 우선 추출
        dollar_match = re.search(r"[$]\s*([\d,]+(?:\.\d+)?)", text)
        if dollar_match:
            try:
                return float(dollar_match.group(1).replace(",", ""))
            except ValueError:
                pass

        # 2. USD 직후 숫자 추출
        usd_match = re.search(r"USD[-:\s]*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if usd_match:
            try:
                return float(usd_match.group(1).replace(",", ""))
            except ValueError:
                pass

        # 3. OCR에서 $ 기호가 '8', '5', 'S'로 오인식된 경우
        ocr_dollar_match = re.search(r"^[85Ss]\s*([1-9]\d{0,2}(?:,\d{3})+(?:\.\d+)?)", text)
        if ocr_dollar_match:
            try:
                return float(ocr_dollar_match.group(1).replace(",", ""))
            except ValueError:
                pass

        # 4. 일반 숫자 추출
        numbers = re.findall(r"[\d,]+(?:\.\d+)?", text)
        if numbers:
            for num_str in reversed(numbers):
                try:
                    val = float(num_str.replace(",", ""))
                    if val > 0:
                        return val
                except ValueError:
                    continue
                    
        return 0.0

    def parse_export_declaration(self, text: str) -> Dict[str, Any]:
        """
        [수출신고필증] 전용 파싱 로직
        - 기업명: '(2) 수출대행자' 항목의 상호명
        - 나라명: '(13) 목적국' 항목의 국가코드 -> 한글 나라명
        - 성과월: '(57) 신고수리일자'의 연월 (YYYY-MM)
        - 수출액: '(49)/(45) 총신고가격(FOB)' 항목의 숫자 금액
        """
        result = {
            "doc_type": DOC_TYPE_DECLARATION,
            "country": "",
            "company": "",
            "month": "",
            "amount": 0.0
        }

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # 1. 기업명 탐색: (2) 수출대행자 앵커
        for i, line in enumerate(lines):
            if any(k in line for k in ["환급신청인", "1:수출", "2제조자", "제조자"]):
                continue
            if any(k in line for k in ["수출대행자", "②", "(2)", "2.", "2 ", "수출화주"]):
                for offset in range(3):
                    if i + offset < len(lines):
                        cand = self.clean_company_name(lines[i + offset])
                        if cand:
                            result["company"] = cand
                            break
                if result["company"]:
                    break

        # 1-2. 전체 텍스트에서 법인 형태 탐색 (Fallback)
        if not result["company"]:
            for line in lines:
                cand = self.clean_company_name(line)
                if cand:
                    result["company"] = cand
                    break

        # 2. 나라명 탐색: (13) 목적국 앵커
        for i, line in enumerate(lines):
            if any(k in line for k in ["목적국", "⑬", "(13)", "13.", "13 "]):
                for offset in range(3):
                    if i + offset < len(lines):
                        c_norm = self.normalize_country(lines[i + offset])
                        if c_norm:
                            result["country"] = c_norm
                            break
                if result["country"]:
                    break

        # 2-2. 국가코드 Fallback
        if not result["country"]:
            tokens = re.split(r"[\s,()（）:;_\-/]+", text.upper())
            for t in tokens:
                if t in self.country_map:
                    result["country"] = self.country_map[t]
                    break

        # 3. 성과월 탐색: (57) 신고수리일자 앵커
        for i, line in enumerate(lines):
            if any(k in line for k in ["신고수리일자", "수리일자", "㊿", "(57)", "57.", "57 "]):
                for offset in range(2):
                    if i + offset < len(lines):
                        m_date = self.normalize_month(lines[i + offset])
                        if m_date:
                            result["month"] = m_date
                            break
                if result["month"]:
                    break

        # 4. 수출액 탐색: (49) / (45) 총신고가격(FOB) 앵커
        for i, line in enumerate(lines):
            if any(k in line for k in ["총신고가격", "49.", "49 ", "(49)", "45.", "45 ", "(45)", "㊺"]):
                for offset in range(3):
                    if i + offset < len(lines):
                        val = self.normalize_amount(lines[i + offset])
                        if val > 0:
                            result["amount"] = val
                            break
                if result["amount"] > 0:
                    break

        # 4-2. 결제금액 / FOB 달러 Fallback
        if result["amount"] == 0.0:
            usd_fob = re.search(r"(?:FOB|EXW|결제금액)[\s\S]{0,60}?(?:USD|[$])[-:\s]*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
            if usd_fob:
                result["amount"] = self.normalize_amount(usd_fob.group(0))

        return result

    def parse_performance_certificate(self, text: str) -> Dict[str, Any]:
        """
        [수출실적증명서] 전용 파싱 로직
        - 기업명: '상호', '기업명', '발급대상자'
        - 나라명: '수출국가', '목적국', '수출국'
        - 성과월: '실적년월', '인정년월', '발급일자' (YYYY-MM)
        - 수출액: '수출액', '실적금액', '합계금액'
        """
        result = {
            "doc_type": DOC_TYPE_PERFORMANCE,
            "country": "",
            "company": "",
            "month": "",
            "amount": 0.0
        }

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        for line in lines:
            if not result["company"] and any(k in line for k in ["상호", "기업명", "발급대상자", "업체명", "신청인"]) and ":" in line:
                result["company"] = self.clean_company_name(line.split(":", 1)[1])

            if not result["country"] and any(k in line for k in ["수출국가", "목적국", "수출국", "바이어국가"]) and ":" in line:
                result["country"] = self.normalize_country(line.split(":", 1)[1])

            if not result["month"] and any(k in line for k in ["실적년월", "인정년월", "실적기간", "발급일자", "일자"]) and ":" in line:
                result["month"] = self.normalize_month(line.split(":", 1)[1])

            if result["amount"] == 0.0 and any(k in line for k in ["수출액", "실적금액", "합계금액", "인정실적", "수출인정실적"]) and ":" in line:
                result["amount"] = self.normalize_amount(line.split(":", 1)[1])

        # Global Fallbacks
        if not result["company"]:
            for line in lines:
                cand = self.clean_company_name(line)
                if cand:
                    result["company"] = cand
                    break

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
            m_amt = re.search(r"(?:USD|[$]|금액)\s*[:：]?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
            if m_amt:
                result["amount"] = self.normalize_amount(m_amt.group(1))

        return result

    def parse(self, text: str, doc_type: str) -> Dict[str, Any]:
        """
        문서 유형에 맞춰 파싱하고, 지정된 JSON 스키마를 준수하여 반환합니다.
        """
        if doc_type == DOC_TYPE_DECLARATION:
            parsed = self.parse_export_declaration(text)
        elif doc_type == DOC_TYPE_PERFORMANCE:
            parsed = self.parse_performance_certificate(text)
        else:
            parsed = self.parse_export_declaration(text)
            alt = self.parse_performance_certificate(text)
            for k in ["company", "country", "month", "amount"]:
                if not parsed.get(k) and alt.get(k):
                    parsed[k] = alt[k]

        return {
            "doc_type": parsed.get("doc_type", DOC_TYPE_UNKNOWN),
            "country": parsed.get("country") or "",
            "company": parsed.get("company") or "",
            "month": parsed.get("month") or "",
            "amount": parsed.get("amount", 0.0)
        }
