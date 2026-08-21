"""
문서 자동 분류 모듈 (Document Classifier)
"""
from typing import Dict, Any, Tuple
from config import (
    DOC_TYPE_PERFORMANCE,
    DOC_TYPE_DECLARATION,
    DOC_TYPE_UNKNOWN,
    CLASSIFICATION_KEYWORDS
)

class DocumentClassifier:
    """
    텍스트 내용 및 키워드 출현 빈도, 고유 서식 특징을 분석하여
    '수출실적증명서'와 '수출신고필증'을 자동 분류하는 클래스.
    """

    def __init__(self):
        self.keywords = CLASSIFICATION_KEYWORDS

    def classify(self, text: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        추출된 텍스트를 기반으로 문서 유형과 신뢰도를 반환합니다.
        
        Args:
            text: 문서에서 추출된 전체 텍스트
            
        Returns:
            Tuple[doc_type, confidence_score, details]
        """
        if not text or len(text.strip()) == 0:
            return DOC_TYPE_UNKNOWN, 0.0, {"reason": "텍스트가 비어있음", "scores": {}}

        clean_text = text.replace(" ", "").replace("\n", "").replace("\t", "").lower()
        
        scores = {
            DOC_TYPE_PERFORMANCE: 0,
            DOC_TYPE_DECLARATION: 0
        }
        
        # 1. 제목 직접 매칭 (가장 높은 가중치)
        if "수출실적증명서" in clean_text or "수출실적확인서" in clean_text or "한국무역협회" in clean_text:
            scores[DOC_TYPE_PERFORMANCE] += 10
        if "수출신고필증" in clean_text or "수출신고서" in clean_text or "신고수리일자" in clean_text or "관세청" in clean_text:
            scores[DOC_TYPE_DECLARATION] += 10

        # 2. 키워드 매칭
        for kw in self.keywords[DOC_TYPE_PERFORMANCE]:
            kw_clean = kw.replace(" ", "").lower()
            if kw_clean in clean_text:
                scores[DOC_TYPE_PERFORMANCE] += 2
                
        for kw in self.keywords[DOC_TYPE_DECLARATION]:
            kw_clean = kw.replace(" ", "").lower()
            if kw_clean in clean_text:
                scores[DOC_TYPE_DECLARATION] += 2

        # 3. 고유 번호/항목 패턴 가중치
        # 수출신고필증 고유 패턴: 신고수리일자, (11)목적국, (48)결제금액, 세관 등
        if any(p in clean_text for p in ["신고수리", "fob", "결제금액", "수출화주", "적재의무기한"]):
            scores[DOC_TYPE_DECLARATION] += 3
            
        # 수출실적증명서 고유 패턴: 실적기간, 인정실적, 직수출, 구매확인서
        if any(p in clean_text for p in ["인정실적", "실적기간", "직수출", "구매확인서", "증명서발급"]):
            scores[DOC_TYPE_PERFORMANCE] += 3

        perf_score = scores[DOC_TYPE_PERFORMANCE]
        decl_score = scores[DOC_TYPE_DECLARATION]
        total_score = perf_score + decl_score

        if total_score == 0:
            return DOC_TYPE_UNKNOWN, 0.0, {"scores": scores, "reason": "일치하는 키워드 없음"}

        if perf_score > decl_score:
            confidence = min(1.0, perf_score / max(10, total_score))
            return DOC_TYPE_PERFORMANCE, round(confidence, 2), {"scores": scores}
        elif decl_score > perf_score:
            confidence = min(1.0, decl_score / max(10, total_score))
            return DOC_TYPE_DECLARATION, round(confidence, 2), {"scores": scores}
        else:
            # 동점인 경우 기본 필증 판정 or 알 수 없음
            return DOC_TYPE_DECLARATION, 0.5, {"scores": scores, "reason": "동점"}
