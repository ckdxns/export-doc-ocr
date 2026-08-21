"""
문서별 데이터 파서 및 정규화 엔진 (Parser & Field Normalizer)
관세청 유니패스(UNI-PASS) 수출신고필증 및 한국무역협회 수출실적증명서 완벽 대응
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

    def clean_company_name(self, raw_name: str) -> str:
        """
        회사명에서 법인 형태를 보존하고 표/컬럼 부산물(PRC, 적재항, 인천항 등)을 깨끗이 제거합니다.
        """
        if not raw_name:
            return ""

        # 1. 접두어 제거 (2. 수출대행자, 수출화주, 상호 등)
        clean = re.sub(r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮㉒㊺㊽㊿0-9.()（）\s]*(?:수출대행자|수출화주|수출자|상호|업체명|신청인)\s*[:：]?", "", raw_name).strip()

        # 2. '(주)기업명' 선행 매칭 (가장 표준적인 법인 표기)
        m_pref = re.search(r"(\((?:주|유|사|재|합|합자)\)\s*[가-힣A-Za-z0-9]+)", clean)
        if m_pref:
            cand = m_pref.group(1).replace(" ", "")
            cand = re.sub(r"레이선$", "레이션", cand)
            return cand

        # 3. '기업명 주식회사' 또는 '기업명(주)' 매칭
        m_suff = re.search(r"([가-힣A-Za-z0-9]{2,}\s*(?:주식회사|유한회사|\((?:주|유)\)))", clean)
        if m_suff:
            cand = m_suff.group(1).strip()
            return cand

        # 4. 뒤따라붙은 테이블 헤더 및 다른 컬럼 데이터 절단
        stop_words = [
            "통관고유부호", "수출자구분", "목적국", "적재항", "선박회사", "선박", "항공사", "PRC", "CN", "US", "USA",
            "인천항", "부산항", "출항예정일자", "적재예정보세구역", "주소", "대표자", "소재지", "사업자등록번호", "정보", "현황"
        ]
        for sw in stop_words:
            if sw in clean:
                clean = clean.split(sw)[0].strip()

        clean = re.sub(r"[()（）:;_\-/]+$", "", clean).strip()
        clean = re.sub(r"레이선$", "레이션", clean)
        return clean

    def normalize_country(self, raw_country: str) -> str:
        """
        국가명 또는 국가 코드를 한글 표준 국가명으로 정규화합니다.
        예: '13. 목적국 CN' -> '중국', 'CN PRC' -> '중국', 'US' -> '미국', 'VN' -> '베트남'
        """
        if not raw_country:
            return "기타"

        # 1. 공백 및 접두어 정리
        clean_text = re.sub(r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮㉒㊺㊽㊿0-9.()（）\s]*목적국\s*[:：]?", "", raw_country).strip()

        # 2. 토큰별 매핑 검사 (CN, PRC, USA 등)
        tokens = re.split(r"[\s,()（）:;_\-/]+", clean_text.upper())
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            if token in self.country_map:
                return self.country_map[token]

        # 3. 전체 문자열 내 등록된 국가명/코드 포함 여부 확인
        for code, kr in self.country_map.items():
            if kr in clean_text or f" {code} " in f" {clean_text.upper()} " or clean_text.upper() == code:
                return kr

        # 4. 등록된 표준 한글 국가명만 허용
        for kr in set(self.country_map.values()):
            if kr in clean_text:
                return kr

        return "미확인국가"

    def normalize_month(self, raw_date: str) -> str:
        """
        날짜 문자열에서 연월(YYYY-MM)을 추출하여 표준화합니다.
        예: '57. 신고수리일자 2025/05/06' -> '2025-05'
        """
        if not raw_date:
            return "2024-01"
            
        clean = raw_date.strip()
        
        # 1. YYYY/MM/DD or YYYY-MM-DD or YYYY.MM.DD
        m = re.search(r"\b(20\d{2})[-./년\s]+(0[1-9]|1[0-2]|\d{1,2})", clean)
        if m:
            year = m.group(1)
            month = m.group(2).zfill(2)
            return f"{year}-{month}"
            
        # 2. 8자리 또는 6자리 연속 숫자 (20250506 or 202505)
        m2 = re.search(r"\b(20\d{2})(0[1-9]|1[0-2])(?:\d{2})?\b", clean)
        if m2:
            return f"{m2.group(1)}-{m2.group(2)}"
            
        return clean[:7] if len(clean) >= 7 else clean

    def normalize_amount(self, raw_amount: Any) -> float:
        """
        수출 금액에서 달러($) 기준 수치 금액을 실수(float)로 추출합니다.
        예: '45. 총신고가격(FOB) $23,202' -> 23202.0
        """
        if isinstance(raw_amount, (int, float)):
            return float(raw_amount)
        if not raw_amount:
            return 0.0
            
        text = str(raw_amount).strip()

        # 1. 달러 기호($) 직후 숫자 우선 추출: $23,202 or $ 23,202.00
        dollar_match = re.search(r"[$]\s*([\d,]+(?:\.\d+)?)", text)
        if dollar_match:
            try:
                return float(dollar_match.group(1).replace(",", ""))
            except ValueError:
                pass

        # 2. USD 직후 숫자 추출: USD 23,202
        usd_match = re.search(r"USD\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if usd_match:
            try:
                return float(usd_match.group(1).replace(",", ""))
            except ValueError:
                pass

        # 3. OCR에서 $ 기호가 '8', '5', 'S'로 오인식된 경우 (예: 823,202 or 523,202 -> 23202.0)
        ocr_dollar_match = re.search(r"^[85Ss]\s*([1-9]\d{1,2}(?:,\d{3})+(?:\.\d+)?)", text)
        if ocr_dollar_match:
            try:
                return float(ocr_dollar_match.group(1).replace(",", ""))
            except ValueError:
                pass

        # 4. 일반 숫자 패턴 추출
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
        [수출신고필증] 전용 파싱 로직 (관세청 UNI-PASS 양식 정밀 매핑)
        """
        result = {
            "doc_type": DOC_TYPE_DECLARATION,
            "company": "",
            "country": "",
            "month": "",
            "amount": 0.0,
            "raw_fields": {}
        }

        # 1. 텍스트 전체에서 선행 '(주)기업명' 정밀 탐색
        m_pref = re.search(r"(\((?:주|유|사|재|합|합자)\)\s*[가-힣A-Za-z0-9]+)", text)
        if m_pref:
            cand = self.clean_company_name(m_pref.group(1))
            if cand and not any(h in cand for h in ["통관", "대표", "소재지", "정보"]):
                result["company"] = cand

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        for i, line in enumerate(lines):
            if (line.startswith("[") and line.endswith("]")) or "정보]" in line or "현황]" in line:
                continue

            # 1-2. 기업명 보완
            if not result["company"] and (any(k in line for k in ["수출대행자", "②", "(2)상호", "수출화주", "수출자"]) or re.search(r"\b2[.]?\s*수출", line)):
                cand = self.clean_company_name(line)
                if cand and len(cand) >= 2 and not any(h in cand for h in ["통관", "대표", "소재지", "정보"]):
                    result["company"] = cand
                    result["raw_fields"]["company"] = line
                elif i + 1 < len(lines):
                    next_cand = self.clean_company_name(lines[i+1])
                    if next_cand and len(next_cand) >= 2:
                        result["company"] = next_cand
                        result["raw_fields"]["company"] = f"{line} / {lines[i+1]}"

            # 2. 나라: 13 목적국 / ⑬ 목적국
            if not result["country"] and ("목적국" in line or "⑬" in line or "(13)" in line or re.search(r"\b13[.]?\s*목적국", line)):
                search_scope = " ".join(lines[i:min(i+3, len(lines))])
                c_norm = self.normalize_country(search_scope)
                if c_norm not in ["기타", "미확인국가"]:
                    result["country"] = c_norm
                    result["raw_fields"]["country"] = search_scope

            # 3. 성과월: 57 신고수리일자 / ㊿ 신고수리일자
            if not result["month"] and any(k in line for k in ["신고수리일자", "수리일자", "㊿", "57.", "57 "]):
                m_date = re.search(r"(\d{4}[-./년\s]+\d{1,2}(?:[-./일\s]+\d{1,2})?)", line)
                if m_date:
                    result["month"] = self.normalize_month(m_date.group(1))
                    result["raw_fields"]["month"] = line
                elif i + 1 < len(lines):
                    m_date_next = re.search(r"(\d{4}[-./년\s]+\d{1,2}(?:[-./일\s]+\d{1,2})?)", lines[i+1])
                    if m_date_next:
                        result["month"] = self.normalize_month(m_date_next.group(1))
                        result["raw_fields"]["month"] = lines[i+1]

            # 4. 수출액: 45 총신고가격(FOB)
            if result["amount"] == 0.0 and any(k in line for k in ["총신고가격", "45.", "45 ", "㊺", "결제금액"]):
                if "$" in line or "USD" in line.upper():
                    val = self.normalize_amount(line)
                    if val > 0:
                        result["amount"] = val
                        result["raw_fields"]["amount"] = line
                elif i + 1 < len(lines):
                    val_next = self.normalize_amount(lines[i+1])
                    if val_next > 0:
                        result["amount"] = val_next
                        result["raw_fields"]["amount"] = lines[i+1]

        # 2차 국가 탐색 (전체 텍스트에서 국가코드)
        if not result["country"]:
            tokens = re.split(r"[\s,()（）:;_\-/]+", text.upper())
            for t in tokens:
                if t in self.country_map:
                    result["country"] = self.country_map[t]
                    break

        # 2차 금액 탐색
        if result["amount"] == 0.0:
            fob_block_match = re.search(r"(?:㊺|45|\(45\)|\(49\)|49)?\s*총신고가격\s*\(?FOB\)?[\s\S]{0,120}?(?:[$]\s*[\d,]+(?:\.\d+)?|USD\s*[\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
            if fob_block_match:
                result["amount"] = self.normalize_amount(fob_block_match.group(0))
                result["raw_fields"]["amount"] = fob_block_match.group(0)
            else:
                m_amount = re.search(r"(?:총신고가격|결제금액)[\s\S]{0,60}?[$]\s*([\d,]+(?:\.\d+)?)", text)
                if m_amount:
                    result["amount"] = self.normalize_amount(m_amount.group(0))
                    result["raw_fields"]["amount"] = m_amount.group(0)

        # 2차 성과월 탐색
        if not result["month"]:
            m_m = re.search(r"(?:신고수리일자|신고일자|수리일자|발급일자)\s*[:：]?\s*(\d{4}[-./년\s]+\d{1,2})", text)
            if m_m:
                result["month"] = self.normalize_month(m_m.group(1))

        return result

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

        m_pref = re.search(r"(\((?:주|유|사|재|합|합자)\)\s*[가-힣A-Za-z0-9]+)", text)
        if m_pref:
            cand = self.clean_company_name(m_pref.group(1))
            if cand:
                result["company"] = cand

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        for line in lines:
            if not result["company"] and any(k in line for k in ["상호", "업체명", "신청인", "수출자", "수출대행자"]) and ":" in line:
                val = self.clean_company_name(line.split(":", 1)[1])
                if val:
                    result["company"] = val
                    result["raw_fields"]["company"] = line

            if not result["country"] and any(k in line for k in ["수출국가", "목적국", "바이어국가", "상대국"]) and ":" in line:
                val = line.split(":", 1)[1].strip()
                result["country"] = self.normalize_country(val)
                result["raw_fields"]["country"] = line

            if not result["month"] and any(k in line for k in ["실적연월", "실적기간", "성과월", "성과연월", "기간"]) and ":" in line:
                val = line.split(":", 1)[1].strip()
                result["month"] = self.normalize_month(val)
                result["raw_fields"]["month"] = line

            if result["amount"] == 0.0 and any(k in line for k in ["수출인정실적", "실적금액", "수출금액", "인정실적", "합계금액", "성약금액", "총신고가격"]) and ":" in line:
                val = line.split(":", 1)[1].strip()
                result["amount"] = self.normalize_amount(val)
                result["raw_fields"]["amount"] = line

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
        문서 유형에 맞춰 파싱하고, 기본값을 채웁니다.
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

        if not parsed.get("company"):
            parsed["company"] = "(주)미상기업"
        if not parsed.get("country"):
            parsed["country"] = "기타"
        if not parsed.get("month"):
            parsed["month"] = "2024-01"
            
        return parsed
