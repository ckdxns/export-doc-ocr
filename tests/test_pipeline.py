"""
통합 테스트 스위트 (Pipeline Verification Test)
"""
import os
import sys
import io
import pytest
import pandas as pd

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.ocr_engine import OCREngine
from modules.document_classifier import DocumentClassifier
from modules.parser import DocumentParser
from modules.data_processor import DataProcessor
from modules.sample_generator import SampleGenerator
from config import DOC_TYPE_PERFORMANCE, DOC_TYPE_DECLARATION, STANDARD_COLUMNS

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
        assert record["company"] == expected["company"], f"Company mismatch in {file_name}"
        assert record["country"] == expected["country"], f"Country mismatch in {file_name}"
        assert record["month"] == expected["month"], f"Month mismatch in {file_name}"
        assert record["amount"] == expected["amount"], f"Amount mismatch in {file_name}"

        parsed_records.append(record)

    # 4. Data Processing & Aggregation
    df = processor.create_dataframe(parsed_records)
    assert len(df) == 4
    for col in STANDARD_COLUMNS:
        assert col in df.columns

    # 5. Company Total Calculation: (주)ABC should have 50000 + 30000 = 80000
    summary = processor.get_company_summary(df)
    abc_summary = summary[summary["기업"] == "(주)ABC"]
    assert len(abc_summary) == 1
    assert abc_summary["총수출 성약액"].values[0] == 80000.0

    # 6. Filter by (주)ABC
    filtered_abc = processor.filter_by_company(df, "(주)ABC")
    assert len(filtered_abc) == 2
    assert list(filtered_abc.columns) == STANDARD_COLUMNS
    assert filtered_abc["수출액"].sum() == 80000.0

    # 7. Excel Generation & Validation
    excel_bytes = processor.export_to_excel_bytes(filtered_abc, "(주)ABC")
    assert len(excel_bytes) > 0

    # Read back generated excel
    read_df = pd.read_excel(io.BytesIO(excel_bytes))
    assert list(read_df.columns) == STANDARD_COLUMNS
    assert len(read_df) == 2
    assert read_df["수출액"].sum() == 80000.0
    print("[SUCCESS] All Pipeline Tests Passed Successfully!")

if __name__ == "__main__":
    test_full_pipeline_samples()
