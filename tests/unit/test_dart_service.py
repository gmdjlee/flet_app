"""Tests for DART service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.dart_service import DartService, DartServiceError


class TestDartService:
    """Test cases for DartService."""

    def test_api_key_required(self):
        """API key is required for DartService initialization."""
        with pytest.raises(ValueError, match="API key is required"):
            DartService(api_key=None)

    def test_api_key_from_env(self, monkeypatch):
        """DartService should read API key from environment variable."""
        monkeypatch.setenv("DART_API_KEY", "test_api_key_12345")
        service = DartService()
        assert service.api_key == "test_api_key_12345"

    def test_explicit_api_key_override(self, monkeypatch):
        """Explicit API key should override environment variable."""
        monkeypatch.setenv("DART_API_KEY", "env_api_key")
        service = DartService(api_key="explicit_api_key")
        assert service.api_key == "explicit_api_key"

    @pytest.mark.asyncio
    async def test_get_corporation_list(self, monkeypatch):
        """Should fetch corporation list from DART API."""
        monkeypatch.setenv("DART_API_KEY", "test_api_key")

        mock_corps = [
            {"corp_code": "00126380", "corp_name": "삼성전자", "stock_code": "005930", "corp_cls": "Y", "modify_date": "20240101"},
            {"corp_code": "00164779", "corp_name": "SK하이닉스", "stock_code": "000660", "corp_cls": "Y", "modify_date": "20240101"},
        ]

        with patch("src.services.dart_service.dart_fss") as mock_dart:
            mock_dart.get_corp_list.return_value = mock_corps

            service = DartService()
            result = await service.get_corporation_list()

            assert len(result) >= 2
            assert any(c["corp_code"] == "00126380" for c in result)

    @pytest.mark.asyncio
    async def test_get_corporation_list_with_market_filter(self, monkeypatch):
        """Should filter corporations by market type."""
        monkeypatch.setenv("DART_API_KEY", "test_api_key")

        mock_corps = [
            {"corp_code": "00126380", "corp_name": "삼성전자", "stock_code": "005930", "corp_cls": "Y", "modify_date": "20240101"},
            {"corp_code": "00164779", "corp_name": "SK하이닉스", "stock_code": "000660", "corp_cls": "K", "modify_date": "20240101"},
        ]

        with patch("src.services.dart_service.dart_fss") as mock_dart:
            mock_dart.get_corp_list.return_value = mock_corps

            service = DartService()
            result = await service.get_corporation_list(market="KOSPI")

            # All results should be KOSPI (corp_cls='Y')
            for corp in result:
                assert corp.get("corp_cls") == "Y"

    @pytest.mark.asyncio
    async def test_get_corporation_info(self, monkeypatch):
        """Should fetch detailed corporation info."""
        monkeypatch.setenv("DART_API_KEY", "test_api_key")

        mock_info = {
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "ceo_nm": "한종희, 경계현",
            "corp_cls": "Y",
            "jurir_no": "1301110006246",
            "bizr_no": "1248100998",
            "adres": "경기도 수원시 영통구 삼성로 129",
            "hm_url": "http://www.samsung.com",
            "est_dt": "19690113",
            "acc_mt": "12",
        }

        with patch("src.services.dart_service.dart_fss") as mock_dart:
            mock_dart.get_corp_info.return_value = mock_info

            service = DartService()
            result = await service.get_corporation_info("00126380")

            assert result["corp_code"] == "00126380"
            assert result["corp_name"] == "삼성전자"
            assert "ceo_nm" in result

    @pytest.mark.asyncio
    async def test_get_financial_statements(self, monkeypatch):
        """Should fetch financial statements for a corporation."""
        monkeypatch.setenv("DART_API_KEY", "test_api_key")

        mock_statements = [
            {
                "corp_code": "00126380",
                "bsns_year": "2023",
                "reprt_code": "11011",
                "fs_div": "CFS",
                "sj_div": "BS",
                "account_id": "ifrs-full_Assets",
                "account_nm": "자산총계",
                "thstrm_amount": "448424000000000",
            },
            {
                "corp_code": "00126380",
                "bsns_year": "2023",
                "reprt_code": "11011",
                "fs_div": "CFS",
                "sj_div": "IS",
                "account_id": "ifrs-full_Revenue",
                "account_nm": "매출액",
                "thstrm_amount": "258935000000000",
            },
        ]

        with patch("src.services.dart_service.dart_fss") as mock_dart:
            mock_dart.get_financial_statement.return_value = mock_statements

            service = DartService()
            result = await service.get_financial_statements(
                corp_code="00126380",
                bsns_year="2023",
                reprt_code="11011"
            )

            assert len(result) >= 2
            assert any(s["account_nm"] == "자산총계" for s in result)
            assert any(s["account_nm"] == "매출액" for s in result)

    @pytest.mark.asyncio
    async def test_get_financial_statements_with_fs_div(self, monkeypatch):
        """Should filter financial statements by fs_div (CFS/OFS)."""
        monkeypatch.setenv("DART_API_KEY", "test_api_key")

        mock_statements = [
            {"fs_div": "CFS", "account_nm": "자산총계", "thstrm_amount": "100"},
            {"fs_div": "OFS", "account_nm": "자산총계", "thstrm_amount": "50"},
        ]

        with patch("src.services.dart_service.dart_fss") as mock_dart:
            mock_dart.get_financial_statement.return_value = mock_statements

            service = DartService()
            result = await service.get_financial_statements(
                corp_code="00126380",
                bsns_year="2023",
                reprt_code="11011",
                fs_div="CFS"
            )

            for stmt in result:
                assert stmt["fs_div"] == "CFS"

    @pytest.mark.asyncio
    async def test_search_corporations(self, monkeypatch):
        """Should search corporations by name."""
        monkeypatch.setenv("DART_API_KEY", "test_api_key")

        mock_corps = [
            {"corp_code": "00126380", "corp_name": "삼성전자", "stock_code": "005930", "corp_cls": "Y"},
            {"corp_code": "00126389", "corp_name": "삼성SDI", "stock_code": "006400", "corp_cls": "Y"},
            {"corp_code": "00107580", "corp_name": "현대자동차", "stock_code": "005380", "corp_cls": "Y"},
        ]

        with patch("src.services.dart_service.dart_fss") as mock_dart:
            mock_dart.get_corp_list.return_value = mock_corps

            service = DartService()
            result = await service.search_corporations("삼성")

            assert len(result) >= 2
            for corp in result:
                assert "삼성" in corp["corp_name"]

    @pytest.mark.asyncio
    async def test_api_error_handling(self, monkeypatch):
        """Should raise DartServiceError on API failure."""
        monkeypatch.setenv("DART_API_KEY", "test_api_key")

        with patch("src.services.dart_service.dart_fss") as mock_dart:
            mock_dart.get_corp_list.side_effect = Exception("API Error")

            service = DartService()
            with pytest.raises(DartServiceError):
                await service.get_corporation_list()

    def test_validate_corp_code(self, monkeypatch):
        """Should validate corporation code format."""
        monkeypatch.setenv("DART_API_KEY", "test_api_key")
        service = DartService()

        # Valid corp_code (8 digits)
        assert service.validate_corp_code("00126380") is True

        # Invalid corp_code
        assert service.validate_corp_code("123456") is False  # Too short
        assert service.validate_corp_code("123456789") is False  # Too long
        assert service.validate_corp_code("abcdefgh") is False  # Non-numeric

    def test_validate_report_code(self, monkeypatch):
        """Should validate report code."""
        monkeypatch.setenv("DART_API_KEY", "test_api_key")
        service = DartService()

        # Valid report codes
        assert service.validate_report_code("11011") is True  # 사업보고서
        assert service.validate_report_code("11012") is True  # 반기보고서
        assert service.validate_report_code("11013") is True  # 1분기보고서
        assert service.validate_report_code("11014") is True  # 3분기보고서

        # Invalid report code
        assert service.validate_report_code("99999") is False
