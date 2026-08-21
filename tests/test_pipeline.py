"""
통합 테스트 스위트 (Pipeline Verification Test with UNIPASS Export Declarations)
"""
import os
import sys
import io
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.ocr_engine import OCREngine
from modules.document_classifier import DocumentClassifier
from modules.parser import DocumentParser
from modules.data_processor import DataProcessor
from modules.sample_generator import SampleGenerator
from config import DOC_TYPE_PERFORMANCE, DOC_TYPE_DECLARATION, STANDARD_COLUMNS

def test_custom_user_examples():
    """
    사용자가 제시한 구체적 서식 사례 테스트:
    - 2. 수출대행자 (주)라온코퍼레이션 -> (주)라온코퍼레이션
    - 13. 목적국 CN -> 중국
    - 57. 신고수리일자 2025/05/06 -> 2025-05
    - 45. 총신고가격(FOB) $23,202 -> 23202.0
    """
    parser = DocumentParser()

    # Case 1: Dot-number notation
    text1 = """
    수출신고필증(적재전, 갑지)
    2. 수출대행자 (주)라온코퍼레이션
    13. 목적국 CN
    45. 총신고가격(FOB) $23,202
    57. 신고수리일자 2025/05/06
    """
    res1 = parser.parse_export_declaration(text1)
    assert res1["company"] == "(주)라온코퍼레이션", f"Got: {res1['company']}"
    assert res1["country"] == "중국", f"Got: {res1['country']}"
    assert res1["month"] == "2025-05", f"Got: {res1['month']}"
    assert res1["amount"] == 23202.0, f"Got: {res1['amount']}"

    # Case 2: Circled number notation (UNI-PASS authentic form)
    text2 = """
    수출신고필증(적재전, 갑지)
    ② 수출대행자 (주)라온코퍼레이션
    ⑬ 목적국 CN PRC
    ㊺ 총신고가격(FOB)
        $ 23,202 (달러화)
        ₩ 34,283,617 (원화)
    ㊿ 신고수리일자 2025/05/06
    """
    res2 = parser.parse_export_declaration(text2)
    assert res2["company"] == "(주)라온코퍼레이션", f"Got: {res2['company']}"
    assert res2["country"] == "중국", f"Got: {res2['country']}"
    assert res2["month"] == "2025-05", f"Got: {res2['month']}"
    assert res2["amount"] == 23202.0, f"Got: {res2['amount']}"

    # Case 3: Country codes USA, JP, VN
    text3 = """
    수출신고필증
    2 수출대행자 (주)글로벌테크
    13 목적국 US
    45 총신고가격 $50,000
    57 신고수리일자 2024-03-15
    """
    res3 = parser.parse_export_declaration(text3)
    assert res3["company"] == "(주)글로벌테크"
    assert res3["country"] == "미국"
    assert res3["month"] == "2024-03"
    assert res3["amount"] == 50000.0

def test_full_pipeline_samples():
    classifier = DocumentClassifier()
    ocr = OCREngine()
    parser = DocumentParser()
    processor = DataProcessor()

    samples = SampleGenerator.generate_all_samples()
    parsed_records = []

    for sample in samples:
        file_name = sample["name"]
        file_bytes = sample["bytes"]
        expected = sample["expected"]

        # 1. OCR / Text extraction
        extracted = ocr.process_file(file_name, file_bytes)
        text = extracted["full_text"]
        assert len(text) > 20, f"Text extraction failed for {file_name}"

        # 2. Document Classification
        doc_type, confidence, details = classifier.classify(text)
        assert doc_type == expected["doc_type"], (
            f"Classification mismatch for {file_name}: expected {expected['doc_type']}, got {doc_type}"
        )
        assert confidence >= 0.5, f"Confidence too low: {confidence}"

        # 3. Parsing
        record = parser.parse(text, doc_type)
        record["file_name"] = file_name
        
        # Verify fields
        assert record["company"] == expected["company"], f"Company mismatch in {file_name}: got {record['company']}"
        assert record["country"] == expected["country"], f"Country mismatch in {file_name}: got {record['country']}"
        assert record["month"] == expected["month"], f"Month mismatch in {file_name}: got {record['month']}"
        assert record["amount"] == expected["amount"], f"Amount mismatch in {file_name}: got {record['amount']}"

        parsed_records.append(record)

    # 4. Data Processing & Aggregation
    df = processor.create_dataframe(parsed_records)
    assert len(df) == 4
    for col in STANDARD_COLUMNS:
        assert col in df.columns

    # 5. Company Total Calculation: (주)라온코퍼레이션 should have 23202 + 50000 = 73202
    summary = processor.get_company_summary(df)
    laon_summary = summary[summary["기업"] == "(주)라온코퍼레이션"]
    assert len(laon_summary) == 1
    assert laon_summary["총수출 성약액"].values[0] == 73202.0

    # 6. Filter by (주)라온코퍼레이션
    filtered_laon = processor.filter_by_company(df, "(주)라온코퍼레이션")
    assert len(filtered_laon) == 2
    assert list(filtered_laon.columns) == STANDARD_COLUMNS
    assert filtered_laon["수출액"].sum() == 73202.0

    # 7. Excel Generation & Validation
    excel_bytes = processor.export_to_excel_bytes(filtered_laon, "(주)라온코퍼레이션")
    assert len(excel_bytes) > 0

    read_df = pd.read_excel(io.BytesIO(excel_bytes))
    assert list(read_df.columns) == STANDARD_COLUMNS
    assert len(read_df) == 2
    assert read_df["수출액"].sum() == 73202.0
    print("[SUCCESS] All Pipeline Tests and Custom User Example Tests Passed!")

if __name__ == "__main__":
    test_custom_user_examples()
    test_full_pipeline_samples()
