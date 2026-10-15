"""Tests for candidate ranking (deterministic keyword scoring)."""

from src.ranking import rank_candidates, score_url


class TestScore:
    def test_profile_link_scores_high(self):
        s = score_url("https://a.co.jp/profile/", "会社概要")
        assert s >= 15

    def test_history_link_scores(self):
        s = score_url("https://a.co.jp/history/", "沿革")
        assert s >= 7

    def test_company_qa_ranks_above_ir_calendar(self):
        qa = score_url("https://a.co.jp/ir/ir_qa/index.html", "Q&A")
        calendar = score_url("https://a.co.jp/ir/calendar/index.html", "IRカレンダー")
        assert qa > calendar

    def test_company_qa_ranks_above_ir_event_transcripts(self):
        company_qa = score_url("https://a.co.jp/ir/ir_qa/index.html", "Q&A")
        event_qa = score_url("https://a.co.jp/ir_library/qa/2025_4q/index.html", "Q&A要旨")
        assert company_qa > event_qa

    def test_plain_product_page_low(self):
        s = score_url("https://a.co.jp/products/x", "製品情報")
        assert score_url("https://a.co.jp/profile/", "会社概要") > s

    def test_penalty_for_news(self):
        assert score_url("https://a.co.jp/news/2024", "会社概要") < score_url("https://a.co.jp/profile/", "会社概要")

    def test_url_path_keywords_count(self):
        # 'company' appears only in the URL path
        assert score_url("https://a.co.jp/company/", "詳しくはこちら") > 0


class TestRank:
    def test_orders_by_score(self):
        ranked = rank_candidates([
            ("https://a.co.jp/news/1", "ニュース"),
            ("https://a.co.jp/profile/", "会社概要"),
            ("https://a.co.jp/history/", "沿革"),
        ])
        assert ranked[0][1] == "https://a.co.jp/profile/"
        assert ranked[1][1] == "https://a.co.jp/history/"

    def test_ties_stable(self):
        ranked = rank_candidates([
            ("https://a.co.jp/b", "同じ"),
            ("https://a.co.jp/a", "同じ"),
        ])
        assert [r[1] for r in ranked] == ["https://a.co.jp/a", "https://a.co.jp/b"]
