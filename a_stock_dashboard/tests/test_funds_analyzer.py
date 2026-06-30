import pandas as pd

from modules.funds_analyzer import label_stock_money_flow, summarize_funds


def test_summarize_funds_detects_volume_expansion():
    result = summarize_funds(
        {"amount_yi": 10000, "amount_5d_avg_yi": 8500, "amount_20d_avg_yi": 8000},
        pd.DataFrame(
            [
                {"sector_name": "证券", "sector_type": "行业", "amount": 900e8, "amount_ratio": 1.5, "score": 70},
                {"sector_name": "黄金", "sector_type": "概念", "amount": 300e8, "amount_ratio": 1.1, "score": 60},
            ]
        ),
        pd.DataFrame([{"stock_name": "红塔证券", "amount_yi": 3.8, "volume_ratio": 1.6, "final_score": 55}]),
    )
    assert result["flow_state"] == "明显放量"
    assert result["top_sector_names"][0] == "证券"


def test_label_stock_money_flow_flags_heavy_down_day():
    result = label_stock_money_flow({"pct_chg": -2.1, "volume_ratio": 1.8, "amount_yi": 4.2, "turnover_rate": 2.0})
    assert result["money_flow_state"] == "放量下跌"
    assert "风险" in result["money_flow_hint"]
