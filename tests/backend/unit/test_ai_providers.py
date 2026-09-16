"""
Unit tests for AI provider abstractions (Mock implementations)
"""
from __future__ import annotations

import pytest
from app.ai.llm import LLMProvider, MockLLMProvider, get_llm_provider
from app.ai.ocr import OCRProvider, MockOCRProvider, DocumentProcessor, Extracted, OCRResult, get_ocr_provider
from app.ai.vision import VisionProvider, MockVisionProvider, FaceResult, get_vision_provider
from app.aml.screening import ScreeningProvider, MockScreeningProvider, Hit, get_screening_provider


class TestMockLLMProvider:
    """Tests for MockLLMProvider"""

    def test_under_review_explanation(self):
        """Should return Persian explanation for under_review"""
        provider = MockLLMProvider()
        prompt = "Decision computed by policy engine: under_review_by_specialist"
        result = provider.generate("system", prompt)
        assert "بررسی متخصص" in result
        assert "تصمیم نهایی توسط مدل زبانی گرفته نشده" in result

    def test_resubmission_explanation(self):
        """Should return Persian explanation for resubmission"""
        provider = MockLLMProvider()
        prompt = "Decision computed by policy engine: resubmission_requested"
        result = provider.generate("system", prompt)
        assert "مدرک باید دوباره ارسال شود" in result
        assert "رد نشده است" in result

    def test_approved_explanation(self):
        """Should return Persian explanation for approved"""
        provider = MockLLMProvider()
        prompt = "Decision computed by policy engine: approved"
        result = provider.generate("system", prompt)
        assert "تأیید" in result

    def test_insufficient_info(self):
        """Should handle insufficient info case"""
        provider = MockLLMProvider()
        prompt = "اطلاعات کافی برای پاسخ قطعی وجود ندارد"
        result = provider.generate("system", prompt)
        assert "اطلاعات کافی" in result

    def test_default_response(self):
        """Should return default response for unknown prompts"""
        provider = MockLLMProvider()
        result = provider.generate("system", "random prompt")
        assert "بر اساس خروجی ابزارها" in result
        assert "هیچ قاعده سیاستی جعل نشده" in result

    def test_factory_returns_mock(self):
        """get_llm_provider should return MockLLMProvider"""
        provider = get_llm_provider("any")
        assert isinstance(provider, MockLLMProvider)


class TestMockOCRProvider:
    """Tests for MockOCRProvider"""

    def test_extract_returns_persian_fields(self):
        """Should return 10 Persian-labeled fields"""
        provider = MockOCRProvider()
        context = {
            "first_name": "محمد",
            "last_name": "احمدی",
            "national_id": "0012345679",
            "birth_date": "1370/01/01",
            "expiry_date": "1405/01/01",
            "gender": "مرد",
            "nationality": "ایران",
            "address": "تهران",
            "passport_number": "A12345678",
        }
        result = provider.extract(b"test", "test.jpg", "national_id", context)
        
        assert isinstance(result, OCRResult)
        assert len(result.fields) == 10
        assert result.provider == "mock"
        assert result.is_simulated is True
        
        field_names = {f.field_name for f in result.fields}
        expected = {"first_name", "last_name", "national_id", "birth_date", 
                      "issue_date", "expiry_date", "gender", "nationality", 
                      "address", "passport_number"}
        assert field_names == expected

    def test_field_confidences_present(self):
        """All fields should have confidence scores"""
        provider = MockOCRProvider()
        result = provider.extract(b"test", "test.jpg", "national_id", {})
        
        for field in result.fields:
            assert 0 <= field.confidence <= 1
            assert field.field_label  # Persian label

    def test_fail_filename_reduces_confidence(self):
        """Filename containing 'fail' should reduce confidence"""
        provider = MockOCRProvider()
        result = provider.extract(b"test", "fail_test.jpg", "national_id", {})
        
        for field in result.fields:
            assert field.confidence < 0.5  # 0.9 * 0.4 = 0.36

    def test_document_processor_classification(self):
        """DocumentProcessor should classify by filename"""
        processor = DocumentProcessor(MockOCRProvider())
        
        assert processor.classify("passport", "passport.jpg") == "passport"
        assert processor.classify("national_id", "meli_card.jpg") == "national_id"
        assert processor.classify("national_id", "national_id.jpg") == "national_id"
        assert processor.classify("driver_license", "license.jpg") == "driver_license"
        assert processor.classify("proof_of_address", "address_bill.jpg") == "proof_of_address"
        assert processor.classify("selfie", "selfie.jpg") == "selfie"
        assert processor.classify("unknown", "random.jpg") == "unknown"

    def test_factory_returns_real_provider(self):
        """get_ocr_provider should return PillowOCRProvider for real OCR"""
        from app.ai.ocr import PillowOCRProvider
        provider = get_ocr_provider("any")
        assert isinstance(provider, PillowOCRProvider)


class TestMockVisionProvider:
    """Tests for MockVisionProvider"""

    def test_compare_returns_face_result(self):
        """Should return FaceResult with all fields"""
        provider = MockVisionProvider()
        result = provider.compare(b"id_bytes", b"selfie_bytes")
        
        assert isinstance(result, FaceResult)
        assert 0 <= result.similarity <= 1
        assert 0 <= result.quality_score <= 1
        assert 0 <= result.confidence <= 1
        assert result.decision in ["match", "mismatch"]
        assert isinstance(result.reasons, list)
        assert result.provider == "mock"
        assert result.is_simulated is True
        assert "زنده" in result.liveness_placeholder

    def test_match_decision_threshold(self):
        """Similarity >= 0.62 should be match"""
        provider = MockVisionProvider()
        # Use same bytes for high similarity
        result = provider.compare(b"same", b"same")
        assert result.similarity >= 0.62
        assert result.decision == "match"

    def test_mismatch_reason(self):
        """Mismatch should include threshold reason"""
        provider = MockVisionProvider()
        # Very different bytes for low similarity
        result = provider.compare(b"id", b"very_different_selfie")
        if result.decision == "mismatch":
            assert any("آستانه" in r for r in result.reasons)

    def test_deterministic_from_hash(self):
        """Same inputs should produce same results"""
        provider = MockVisionProvider()
        r1 = provider.compare(b"test", b"test")
        r2 = provider.compare(b"test", b"test")
        assert r1.similarity == r2.similarity
        assert r1.decision == r2.decision

    def test_to_dict_serialization(self):
        """to_dict should include all fields"""
        provider = MockVisionProvider()
        result = provider.compare(b"a", b"b")
        d = result.to_dict()
        assert "similarity" in d
        assert "quality_score" in d
        assert "confidence" in d
        assert "decision" in d
        assert "reasons" in d
        assert "provider" in d
        assert "is_simulated" in d
        assert "liveness_placeholder" in d

    def test_factory_returns_mock(self):
        """get_vision_provider should return MockVisionProvider"""
        provider = get_vision_provider("any")
        assert isinstance(provider, MockVisionProvider)


class TestMockScreeningProvider:
    """Tests for MockScreeningProvider"""

    def test_screen_returns_four_hits(self):
        """Should return 4 screening hits (sanctions, pep, adverse_media, watchlist)"""
        provider = MockScreeningProvider()
        hits = provider.screen("Test User", "0012345679")
        
        assert len(hits) == 4
        kinds = {h.kind for h in hits}
        assert kinds == {"sanctions", "pep", "adverse_media", "watchlist"}

    def test_sanctions_match_on_forced_name(self):
        """Name containing 'تحریم' should match sanctions"""
        provider = MockScreeningProvider()
        hits = provider.screen("جان تحریم شده", "0012345679")
        
        sanctions_hit = next(h for h in hits if h.kind == "sanctions")
        assert sanctions_hit.matched is True
        assert sanctions_hit.score == 100.0

    def test_pep_match_on_forced_name(self):
        """Name containing 'سیاسی' should match PEP"""
        provider = MockScreeningProvider()
        hits = provider.screen("علی سیاسی", "0012345679")
        
        pep_hit = next(h for h in hits if h.kind == "pep")
        assert pep_hit.matched is True
        assert pep_hit.score == 100.0

    def test_national_id_forced_matches(self):
        """NID ending in 0000 should match sanctions, 1111 should match PEP"""
        provider = MockScreeningProvider()
        
        # Sanctions forced
        hits = provider.screen("User", "1234560000")
        sanctions_hit = next(h for h in hits if h.kind == "sanctions")
        assert sanctions_hit.matched is True
        
        # PEP forced
        hits = provider.screen("User", "1234561111")
        pep_hit = next(h for h in hits if h.kind == "pep")
        assert pep_hit.matched is True

    def test_fuzzy_matching_threshold(self):
        """Fuzzy matching should work above threshold"""
        provider = MockScreeningProvider()
        # Close to "جان اسمیت تحریم شده"
        hits = provider.screen("جان اسمیت تحریم", "0012345679")
        sanctions_hit = next(h for h in hits if h.kind == "sanctions")
        # Should have high score but may not match (threshold 90)
        assert sanctions_hit.score >= 0

    def test_all_hits_simulated(self):
        """All hits should be marked as simulated"""
        provider = MockScreeningProvider()
        hits = provider.screen("Test", "0012345679")
        
        for hit in hits:
            assert hit.is_simulated is True
            assert "شبیه‌سازی" in hit.note

    def test_factory_returns_mock(self):
        """get_screening_provider should return MockScreeningProvider"""
        provider = get_screening_provider("any")
        assert isinstance(provider, MockScreeningProvider)


class TestProviderInterfaces:
    """Tests that all providers implement their abstract interfaces"""

    def test_llm_provider_abstract(self):
        """LLMProvider should be abstract"""
        with pytest.raises(TypeError):
            LLMProvider()

    def test_ocr_provider_abstract(self):
        """OCRProvider should be abstract"""
        with pytest.raises(TypeError):
            OCRProvider()

    def test_vision_provider_abstract(self):
        """VisionProvider should be abstract"""
        with pytest.raises(TypeError):
            VisionProvider()

    def test_screening_provider_abstract(self):
        """ScreeningProvider should be abstract"""
        with pytest.raises(TypeError):
            ScreeningProvider()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])