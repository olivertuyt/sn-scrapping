"""Tests for extraction validation (deterministic, TDD per project policy)."""

from src.schema import CompanyData, FieldDecision, validate_company, validate_decision


def _found(value="テスト", url="https://a.co.jp/p", evidence="ラベル: テスト"):
    return FieldDecision(value=value, status="FOUND", source_url=url, evidence=evidence)


class TestNullRules:
    def test_null_with_not_found_ok(self):
        d = FieldDecision()
        assert validate_decision("capital", d, None) == []

    def test_null_with_found_is_error(self):
        d = FieldDecision(value=None, status="FOUND")
        assert validate_decision("capital", d, None) != []

    def test_not_found_with_evidence_is_error(self):
        d = FieldDecision(value=None, status="NOT_FOUND", evidence="x")
        assert validate_decision("capital", d, None) != []

    def test_empty_string_value_is_null(self):
        d = FieldDecision(value="  ", status="FOUND", source_url="u", evidence="e")
        assert validate_decision("capital", d, None) != []


class TestEvidenceRules:
    def test_found_without_source_url_is_error(self):
        d = FieldDecision(value="x", status="FOUND", evidence="e")
        assert validate_decision("capital", d, None) != []

    def test_evidence_not_in_page_is_error(self):
        d = _found(evidence="ラベル: テスト")
        assert validate_decision("capital", d, "全然違うテキスト") != []

    def test_evidence_in_page_ok(self):
        d = _found(evidence="ラベル: テスト")
        assert validate_decision("capital", d, "前書き ラベル: テスト 後書き") == []

    def test_evidence_unicode_space_normalized(self):
        # Japanese pages use em-space U+2003 / ideographic U+3000 in addresses;
        # the model normalizes them to plain spaces — content must still match
        d = _found(value="東京都港区1-1", evidence="本社 東京都港区1-1")
        assert validate_decision("head_office_address", d, "本社 東京都港区1-1") == []
        assert validate_decision("head_office_address", d, "本社　東京都港区1-1") == []

    def test_evidence_content_mismatch_still_fails(self):
        d = _found(evidence="ラベル: テスト")
        assert validate_decision("capital", d, "ラベル: 別の値") != []

    def test_value_must_be_supported_by_evidence(self):
        d = _found(value="999億円", evidence="資本金 1億円")
        assert validate_decision("capital", d, "資本金 1億円") != []

    def test_capital_cannot_match_inside_a_larger_number(self):
        d = _found(value="1億円", evidence="資本金 11億円")
        assert validate_decision("capital", d, "資本金 11億円") != []

    def test_every_list_value_must_be_supported_by_evidence(self):
        d = FieldDecision(
            value=["代表取締役 田中太郎", "代表取締役 山田花子"],
            status="MULTIPLE_CANDIDATES",
            source_url="https://a.co.jp/p",
            evidence="代表取締役 田中太郎",
        )
        assert validate_decision("representative", d, "代表取締役 田中太郎") != []

    def test_page_text_none_skips_verbatim_check(self):
        d = _found()
        assert validate_decision("capital", d, None) == []


class TestMonthRule:
    def test_month_in_value_but_not_evidence_is_inference(self):
        d = _found(value="1911年4月", evidence="設立 1911年")
        problems = validate_decision("established_year_month", d, "設立 1911年")
        assert any("month inference" in p for p in problems)

    def test_month_in_both_ok(self):
        d = _found(value="1911年4月", evidence="設立 1911年4月")
        assert validate_decision("established_year_month", d, "設立 1911年4月") == []

    def test_year_only_ok(self):
        d = _found(value="1911年", evidence="設立 1911年")
        assert validate_decision("established_year_month", d, "設立 1911年") == []

    def test_era_year_only_ok(self):
        d = _found(value="明治44年", evidence="設立 明治44年")
        assert validate_decision("established_year_month", d, "設立 明治44年") == []

    def test_multivalue_month_check(self):
        d = FieldDecision(
            value=["1911年", "1911年4月"],
            status="MULTIPLE_CANDIDATES",
            source_url="https://a.co.jp/p",
            evidence="設立 1911年",
        )
        problems = validate_decision("established_year_month", d, "設立 1911年")
        assert problems  # the 4月 entry has no month in evidence

    def test_gregorian_month_with_era_between_year_and_month(self):
        d = _found(
            value="1998年6月",
            evidence="平成10年（1998年） 6月 タマホーム株式会社を設立",
        )
        assert validate_decision("established_year_month", d, d.evidence) == []

    def test_gregorian_month_from_era_evidence(self):
        d = _found(value="1964年7月", evidence="会社の設立はいつですか？ 昭和39年7月です。")
        assert validate_decision("established_year_month", d, d.evidence) == []

    def test_gregorian_month_requires_matching_year_and_month(self):
        d = _found(value="1965年7月", evidence="会社の設立はいつですか？ 昭和39年7月です。")
        assert validate_decision("established_year_month", d, d.evidence) != []


class TestCompanyLevel:
    def test_validate_company_uses_page_text_by_url(self):
        c = CompanyData(company_name="X", seed_url="https://a.co.jp/")
        c.capital = _found()
        texts = {"https://a.co.jp/p": "ラベル: テスト"}
        assert validate_company(c, texts) == []

    def test_validate_company_catches_wrong_url(self):
        c = CompanyData(company_name="X", seed_url="https://a.co.jp/")
        c.capital = _found()
        texts = {"https://a.co.jp/other": "ラベル: テスト"}
        assert validate_company(c, texts) != []
