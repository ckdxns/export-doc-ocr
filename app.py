"""
수출실적증명서 및 수출신고필증 OCR 데이터 자동 추출 및 분석 웹 애플리케이션 (Streamlit)
"""
import io
import time
import streamlit as st
import pandas as pd
from modules.ocr_engine import OCREngine
from modules.document_classifier import DocumentClassifier
from modules.parser import DocumentParser
from modules.data_processor import DataProcessor
from modules.sample_generator import SampleGenerator
from config import (
    DOC_TYPE_PERFORMANCE,
    DOC_TYPE_DECLARATION,
    DOC_TYPE_UNKNOWN,
    STANDARD_COLUMNS,
    SUPPORTED_EXTENSIONS
)

# 페이지 설정
st.set_page_config(
    page_title="수출 문서 OCR 분석 및 총수출 성약액 산출 시스템",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS 스타일링
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .badge-perf {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-decl {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# 모듈 인스턴스 캐싱
@st.cache_resource
def get_services():
    ocr = OCREngine()
    classifier = DocumentClassifier()
    parser = DocumentParser()
    processor = DataProcessor()
    return ocr, classifier, parser, processor

ocr_engine, classifier, parser, processor = get_services()

# 세션 상태 초기화
if "processed_results" not in st.session_state:
    st.session_state["processed_results"] = []
if "df_records" not in st.session_state:
    st.session_state["df_records"] = pd.DataFrame(columns=STANDARD_COLUMNS)

# --- 사이드바 ---
with st.sidebar:
    st.header("⚙️ 시스템 설정 및 샘플")
    
    st.markdown("### 🧪 원클릭 샘플 테스트")
    st.info("수출실적증명서 및 수출신고필증 표준 서식 샘플 4종을 즉시 로드하여 파싱 및 엑셀 다운로드를 테스트할 수 있습니다.")
    
    if st.button("🚀 샘플 문서 일괄 로드 및 분석", use_container_width=True, type="primary"):
        with st.spinner("샘플 문서를 생성하고 OCR 파이프라인을 실행하는 중..."):
            samples = SampleGenerator.generate_all_samples()
            records = []
            results = []
            
            for s in samples:
                extracted = ocr_engine.process_file(s["name"], s["bytes"])
                doc_type, conf, details = classifier.classify(extracted["full_text"])
                parsed = parser.parse(extracted["full_text"], doc_type)
                parsed["file_name"] = s["name"]
                records.append(parsed)
                results.append({
                    "file_name": s["name"],
                    "doc_type": doc_type,
                    "confidence": conf,
                    "text": extracted["full_text"],
                    "parsed": parsed
                })
                
            st.session_state["processed_results"] = results
            st.session_state["df_records"] = processor.create_dataframe(records)
            st.success(f"샘플 문서 {len(samples)}건 분석 완료!")

    st.markdown("---")
    st.markdown("### 📖 표준 출력 스키마")
    st.markdown("""
    - **나라**: 바이어/목적국 (한글 표준명)
    - **기업**: 수출자/상호
    - **성과월**: YYYY-MM 형식
    - **수출액**: 미화(USD) 기준 금액
    """)
    
    if st.button("🗑️ 분석 결과 초기화", use_container_width=True):
        st.session_state["processed_results"] = []
        st.session_state["df_records"] = pd.DataFrame(columns=STANDARD_COLUMNS)
        st.rerun()

# --- 메인 헤더 ---
st.markdown('<div class="main-title">📑 수출실적증명서 & 수출신고필증 데이터 자동 추출 시스템</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">PDF 및 스캔 이미지 문서를 업로드하면 OCR을 통해 서식을 자동 분류하고 [나라, 기업, 성과월, 수출액] 데이터를 추출하여 기업별 총수출 성약액을 계산합니다.</div>', unsafe_allow_html=True)

# --- 1단계: 파일 업로드 섹션 ---
st.subheader("1️⃣ 문서 업로드 (PDF / 이미지)")
uploaded_files = st.file_uploader(
    "수출실적증명서 또는 수출신고필증 파일들을 업로드하세요 (단일 및 다중 업로드 지원)",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("⚡ 업로드된 파일 OCR 분석 시작", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        records = []
        results = []
        total = len(uploaded_files)
        
        for idx, file in enumerate(uploaded_files):
            status_text.text(f"[{idx+1}/{total}] '{file.name}' OCR 및 서식 분석 중...")
            file_bytes = file.read()
            
            # 1. OCR 텍스트 추출
            extracted = ocr_engine.process_file(file.name, file_bytes)
            
            # 2. 문서 분류
            doc_type, conf, details = classifier.classify(extracted["full_text"])
            
            # 3. 데이터 파싱
            parsed = parser.parse(extracted["full_text"], doc_type)
            parsed["file_name"] = file.name
            
            records.append(parsed)
            results.append({
                "file_name": file.name,
                "doc_type": doc_type,
                "confidence": conf,
                "text": extracted["full_text"],
                "parsed": parsed
            })
            progress_bar.progress((idx + 1) / total)

        st.session_state["processed_results"] = results
        st.session_state["df_records"] = processor.create_dataframe(records)
        status_text.empty()
        progress_bar.empty()
        st.success(f"총 {total}건의 문서 분석이 완료되었습니다!")

processed_results = st.session_state.get("processed_results", [])
df_records = st.session_state.get("df_records", pd.DataFrame(columns=STANDARD_COLUMNS))

# --- 2단계: 문서 분류 및 파싱 상세 검토 ---
if processed_results:
    st.markdown("---")
    st.subheader("2️⃣ 문서별 자동 분류 및 파싱 상세")
    
    cols = st.columns(len(processed_results) if len(processed_results) <= 4 else 4)
    for i, item in enumerate(processed_results):
        col_idx = i % 4
        with cols[col_idx]:
            badge_class = "badge-perf" if item["doc_type"] == DOC_TYPE_PERFORMANCE else "badge-decl"
            st.markdown(f"""
            <div style="border: 1px solid #E5E7EB; border-radius: 8px; padding: 12px; margin-bottom: 12px; background: #FFFFFF;">
                <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="{item['file_name']}">📄 {item['file_name']}</div>
                <div style="margin-bottom: 8px;"><span class="{badge_class}">{item['doc_type']}</span> <span style="font-size: 0.8rem; color: #6B7280;">(신뢰도: {int(item['confidence']*100)}%)</span></div>
                <div style="font-size: 0.85rem; color: #374151;">
                    • <b>기업</b>: {item['parsed']['company']}<br>
                    • <b>국가</b>: {item['parsed']['country']}<br>
                    • <b>성과월</b>: {item['parsed']['month']}<br>
                    • <b>수출액</b>: ${item['parsed']['amount']:,.0f}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with st.expander("🔍 문서별 추출 원본 텍스트 및 상세 로그 확인"):
        for res in processed_results:
            st.markdown(f"**[{res['doc_type']}] {res['file_name']}** (신뢰도: {res['confidence'] * 100:.1f}%)")
            st.code(res["text"][:800] + ("..." if len(res["text"]) > 800 else ""), language="text")

# --- 3단계 & 4단계: 기업별 필터링, 데이터 편집(v1.3) & 총수출 성약액 KPI ---
if not df_records.empty:
    st.markdown("---")
    st.subheader("3️⃣ 기업별 필터링 및 데이터 편집/검토")

    df_current = df_records.copy()
    company_list = ["전체"] + sorted(list(df_current["기업"].unique()))
    
    col_filter, col_reset = st.columns([3, 1])
    with col_filter:
        selected_company = st.selectbox("🏢 조회 및 다운로드할 기업을 선택하세요:", company_list)

    # 선택된 기업 데이터 필터링
    if selected_company == "전체":
        display_df = df_current[STANDARD_COLUMNS].copy()
    else:
        display_df = df_current[df_current["기업"] == selected_company][STANDARD_COLUMNS].copy()

    # KPI 지표 카드
    total_amount = display_df["수출액"].sum()
    total_count = len(display_df)
    unique_countries = display_df["나라"].nunique()
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(
            label=f"💰 {'전체 기업' if selected_company == '전체' else selected_company} 총수출 성약액",
            value=f"${total_amount:,.0f} USD"
        )
    with kpi2:
        st.metric(label="📄 처리된 수출 건수", value=f"{total_count} 건")
    with kpi3:
        st.metric(label="🌍 진출 국가 수", value=f"{unique_countries} 개국")
    with kpi4:
        st.metric(label="🏢 대상 기업 수", value=f"{df_current['기업'].nunique()} 개사")

    # 데이터 편집기 (v1.3 요구사항)
    st.markdown("##### ✏️ 데이터 편집 테이블 (OCR 인식값 수정 가능)")
    st.caption("💡 OCR 파싱 결과 중 수정이 필요한 항목(나라, 기업명, 성과월, 수출액)을 셀에서 직접 더블클릭하여 수정할 수 있습니다.")

    edited_df = st.data_editor(
        display_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "나라": st.column_config.TextColumn("나라", help="수출 목적국/바이어 국가"),
            "기업": st.column_config.TextColumn("기업", help="수출자/상호"),
            "성과월": st.column_config.TextColumn("성과월", help="YYYY-MM 형식"),
            "수출액": st.column_config.NumberColumn("수출액 (USD)", format="$%d", help="수출 결제/인정 금액")
        }
    )

    # --- 5단계: 엑셀 파일 다운로드 ---
    st.markdown("---")
    st.subheader("4️⃣ 표준 엑셀(.xlsx) 파일 다운로드")

    excel_bytes = processor.export_to_excel_bytes(edited_df, selected_company)
    file_label = f"수출실적내역_{selected_company}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx"

    col_btn1, col_btn2 = st.columns([2, 2])
    with col_btn1:
        st.download_button(
            label=f"📥 '{selected_company}' 세부 내역 엑셀 다운로드 (.xlsx)",
            data=excel_bytes,
            file_name=file_label,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )
    with col_btn2:
        csv_data = edited_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label=f"📄 '{selected_company}' 세부 내역 CSV 다운로드 (.csv)",
            data=csv_data,
            file_name=file_label.replace(".xlsx", ".csv"),
            mime="text/csv",
            use_container_width=True
        )

    # 기업별 / 국가별 요약 차트
    with st.expander("📊 시각화 차트 및 통계 요약"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**기업별 총수출 성약액**")
            summary_comp = df_current.groupby("기업")["수출액"].sum().reset_index()
            st.bar_chart(summary_comp.set_index("기업"))
        with c2:
            st.markdown("**국가별 수출액 비중**")
            summary_country = edited_df.groupby("나라")["수출액"].sum().reset_index()
            st.bar_chart(summary_country.set_index("나라"))
else:
    st.info("👆 위 파일 업로더를 통해 문서를 업로드하거나, 사이드바의 '샘플 문서 일괄 로드 및 분석' 버튼을 눌러보세요.")
