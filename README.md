# 📑 수출실적증명서 및 수출신고필증 OCR 자동 파싱 & 성약액 집계 시스템

기업의 **수출실적증명서** 및 **수출신고필증**(PDF 또는 이미지)을 업로드하면 OCR 및 지능형 문서 파싱을 통해 필수 항목(`[나라, 기업, 성과월, 수출액]`)을 자동 추출하고, 기업별 **총수출 성약액**을 산출하여 엑셀(.xlsx) 파일로 다운로드할 수 있는 웹 애플리케이션입니다.

---

## 🌟 주요 기능

1. **지능형 문서 자동 분류 (Document Classifier)**
   - 한국무역협회 `수출실적증명서`와 관세청 `수출신고필증` 서식을 키워드 및 패턴 기반으로 100% 자동 판별
2. **하이브리드 OCR & 텍스트 추출 (OCR Engine)**
   - 디지털 PDF: PyMuPDF 기반 무손실 텍스트 고속 추출
   - 스캔 PDF & 이미지(PNG/JPG): OpenCV 이미지 전처리 + EasyOCR (한글/영문)
3. **서식 맞춤형 정보 정규화 (Parser)**
   - 수출신고필증: `(5)수출화주` $\rightarrow$ 기업, `(11)목적국` $\rightarrow$ 나라, `(52)신고수리일자` $\rightarrow$ 성과월(YYYY-MM), `(48)결제금액` $\rightarrow$ 수출액
   - 수출실적증명서: `상호` $\rightarrow$ 기업, `수출국가` $\rightarrow$ 나라, `실적연월` $\rightarrow$ 성과월(YYYY-MM), `인정실적` $\rightarrow$ 수출액
4. **기업별 총수출 성약액 자동 집계 & KPI 대시보드**
   - 두 서식의 데이터가 통합되어 선택한 기업의 총수출 성약액 및 건수 실시간 계산
5. **인터랙티브 데이터 편집 테이블 (v1.3 반영)**
   - OCR 인식 결과 중 수정이 필요한 항목을 UI에서 직접 편집 가능
6. **표준 4개 컬럼 엑셀(.xlsx) 다운로드**
   - `[나라, 기업, 성과월, 수출액]` 형식의 정렬 및 셀 서식(콤마 포맷)이 적용된 엑셀 파일 즉시 다운로드
7. **원클릭 샘플 문서 테스트 지원**
   - 별도 파일 없이도 사이드바 버튼 클릭 한 번으로 4종의 표준 샘플 문서를 생성하여 즉시 테스트 가능

---

## 📁 프로젝트 구조

```
final_/
├── app.py                     # Streamlit 웹 애플리케이션 메인
├── config.py                  # 국가 매핑, 키워드, 표준 컬럼 등 설정
├── modules/
│   ├── document_classifier.py # 서식 자동 분류기
│   ├── ocr_engine.py          # PyMuPDF + EasyOCR 하이브리드 엔진
│   ├── parser.py              # 서식별 정규식 및 키워드 추출 파서
│   ├── data_processor.py      # 데이터프레임 변환, 집계 및 엑셀 스타일러
│   └── sample_generator.py    # 테스트용 샘플 문서 PDF 생성기
├── tests/
│   └── test_pipeline.py       # 전 과정 자동화 검증 단위/통합 테스트
├── requirements.txt           # 필수 패키지 목록
└── README.md                  # 프로젝트 설명 문서
```

---

## 🚀 실행 방법

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. Streamlit 웹 애플리케이션 실행
```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 주소로 접속하여 사용하실 수 있습니다.
