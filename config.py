"""
설정 및 상수 정의 모듈
"""

# 지원되는 파일 확장자
SUPPORTED_EXTENSIONS = [".pdf", ".png", ".jpg", ".jpeg"]

# 표준 데이터 컬럼명
STANDARD_COLUMNS = ["나라", "기업", "성과월", "수출액"]

# 문서 유형 상수
DOC_TYPE_PERFORMANCE = "수출실적증명서"
DOC_TYPE_DECLARATION = "수출신고필증"
DOC_TYPE_UNKNOWN = "미확인서식"

# 문서 분류 키워드
CLASSIFICATION_KEYWORDS = {
    DOC_TYPE_PERFORMANCE: [
        "수출실적증명서", "수출실적확인서", "수출실적", "한국무역협회", "한국무역통계진흥원",
        "실적기간", "발급번호", "직수출실적", "수출인정실적", "무역협회"
    ],
    DOC_TYPE_DECLARATION: [
        "수출신고필증", "수출신고서", "신고수리일자", "신고번호", "관세청",
        "수출자", "목적국", "결제금액", "FOB금액", "총신고가격", "신고일자",
        "선적조건", "세관", "물품소재지"
    ]
}

# 국가명 정규화 매핑 사전
COUNTRY_MAP = {
    "US": "미국", "USA": "미국", "UNITED STATES": "미국", "미합중국": "미국",
    "CN": "중국", "CHINA": "중국",
    "JP": "일본", "JAPAN": "일본",
    "VN": "베트남", "VIETNAM": "베트남",
    "DE": "독일", "GERMANY": "독일",
    "GB": "영국", "UK": "영국", "UNITED KINGDOM": "영국",
    "SG": "싱가포르", "SINGAPORE": "싱가포르",
    "TW": "대만", "TAIWAN": "대만",
    "IN": "인도", "INDIA": "인도",
    "ID": "인도네시아", "INDONESIA": "인도네시아",
    "TH": "태국", "THAILAND": "태국",
    "MY": "말레이시아", "MALAYSIA": "말레이시아",
    "AU": "호주", "AUSTRALIA": "호주",
    "CA": "캐나다", "CANADA": "캐나다",
    "HK": "홍콩", "HONG KONG": "홍콩",
    "MX": "멕시코", "MEXICO": "멕시코",
    "BR": "브라질", "BRAZIL": "브라질",
    "FR": "프랑스", "FRANCE": "프랑스",
    "IT": "이탈리아", "ITALY": "이탈리아",
    "NL": "네덜란드", "NETHERLANDS": "네덜란드",
    "PH": "필리핀", "PHILIPPINES": "필리핀",
    "RU": "러시아", "RUSSIA": "러시아",
}
