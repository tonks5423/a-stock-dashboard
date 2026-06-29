from __future__ import annotations


def sector_state(score: float) -> str:
    if score >= 80:
        return "主线强板块"
    if score >= 60:
        return "活跃板块"
    if score >= 40:
        return "普通板块"
    return "弱势板块"


def add_sector_state(sectors):
    data = sectors.copy()
    data["state"] = data["score"].apply(sector_state)
    return data
