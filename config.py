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
        "수출대행자", "수출자", "목적국", "결제금액", "FOB금액", "총신고가격", "신고일자",
        "선적조건", "세관", "물품소재지", "UNI-PASS", "적재전"
    ]
}

# 국가명 및 국가코드 정규화 매핑 사전
COUNTRY_MAP = {
    "CN": "중국", "PRC": "중국", "CHN": "중국", "CHINA": "중국", "중화인민공화국": "중국",
    "US": "미국", "USA": "미국", "UNITED STATES": "미국", "미합중국": "미국",
    "JP": "일본", "JPN": "일본", "JAPAN": "일본",
    "VN": "베트남", "VNM": "베트남", "VIETNAM": "베트남",
    "DE": "독일", "DEU": "독일", "GERMANY": "독일",
    "GB": "영국", "GBR": "영국", "UK": "영국", "UNITED KINGDOM": "영국",
    "SG": "싱가포르", "SGP": "싱가포르", "SINGAPORE": "싱가포르",
    "TW": "대만", "TWN": "대만", "TAIWAN": "대만",
    "HK": "홍콩", "HKG": "홍콩", "HONG KONG": "홍콩",
    "IN": "인도", "IND": "인도", "INDIA": "인도",
    "ID": "인도네시아", "IDN": "인도네시아", "INDONESIA": "인도네시아",
    "TH": "태국", "THA": "태국", "THAILAND": "태국",
    "MY": "말레이시아", "MYS": "말레이시아", "MALAYSIA": "말레이시아",
    "AU": "호주", "AUS": "호주", "AUSTRALIA": "호주",
    "CA": "캐나다", "CAN": "캐나다", "CANADA": "캐나다",
    "MX": "멕시코", "MEX": "멕시코", "MEXICO": "멕시코",
    "BR": "브라질", "BRA": "브라질", "BRAZIL": "브라질",
    "FR": "프랑스", "FRA": "프랑스", "FRANCE": "프랑스",
    "IT": "이탈리아", "ITA": "이탈리아", "ITALY": "이탈리아",
    "NL": "네덜란드", "NLD": "네덜란드", "NETHERLANDS": "네덜란드",
    "PH": "필리핀", "PHL": "필리핀", "PHILIPPINES": "필리핀",
    "RU": "러시아", "RUS": "러시아", "RUSSIA": "러시아",
    "ES": "스페인", "ESP": "스페인", "SPAIN": "스페인",
    "CH": "스위스", "CHE": "스위스", "SWITZERLAND": "스위스",
    "AE": "아랍에미리트", "ARE": "아랍에미리트", "UAE": "아랍에미리트",
    "SA": "사우디아라비아", "SAU": "사우디아라비아", "SAUDI ARABIA": "사우디아라비아",
    "PL": "폴란드", "POL": "폴란드", "POLAND": "폴란드",
    "TR": "튀르키예", "TUR": "튀르키예", "TURKEY": "튀르키예"
}
