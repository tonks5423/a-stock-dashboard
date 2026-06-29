from modules.score_engine import calculate_final_stock_score, calculate_market_score, calculate_sector_score


def test_market_score_returns_reason():
    result = calculate_market_score(
        {
            "up_count": 3000,
            "down_count": 1800,
            "amount_yi": 9500,
            "limit_up_count": 60,
            "limit_down_count": 8,
            "index_avg_pct": 0.8,
        }
    )
    assert 0 <= result["score"] <= 100
    assert result["reason"]


def test_sector_score_returns_reason():
    result = calculate_sector_score({"pct_chg": 2, "pct_chg_5d": 5, "pct_chg_10d": 8, "amount_ratio": 1.4, "limit_up_count": 5, "relative_market_pct": 1.2})
    assert 0 <= result["score"] <= 100
    assert "今日涨跌幅" in result["reason"]


def test_final_stock_score_clamped():
    result = calculate_final_stock_score(100, 100, 100, 100, 100, 120)
    assert result["score"] == 0
    assert result["reason"] == "回避"
