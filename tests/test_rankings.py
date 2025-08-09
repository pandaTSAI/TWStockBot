# =========================
# File: tests/test_rankings.py
# =========================
import json
import datetime as dt
import pathlib
import pytest

from app import rankings

FIXTURE_TWSE = pathlib.Path(__file__).parent / "fixtures" / "mi_index_sample.json"
FIXTURE_TPEX = pathlib.Path(__file__).parent / "fixtures" / "tpex_quotes_sample.json"





@pytest.fixture()
def mi_payload():
    with open(FIXTURE_TWSE, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture()
def tpex_payload():
    with open(FIXTURE_TPEX, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_top_gainers_all(monkeypatch, mi_payload, tpex_payload):
    async def fake_twse(date: dt.date):
        return mi_payload

    async def fake_tpex(date: dt.date):
        return tpex_payload

    monkeypatch.setattr(rankings, "_fetch_twse_mi_index", fake_twse)
    monkeypatch.setattr(rankings, "_fetch_tpex_quotes", fake_tpex)

    result = await rankings.top_gainers(limit=3, date=dt.date(2025, 8, 8), market="ALL")
    assert len(result["items"]) == 3
    assert result["items"][0]["symbol"] == "8431"  # TPEx +10% beats TWSE +5%
    assert result["items"][0]["market"] == "TPEX"


@pytest.mark.asyncio
async def test_top_losers_tpex(monkeypatch, tpex_payload):
    async def fake_tpex(date: dt.date):
        return tpex_payload

    monkeypatch.setattr(rankings, "_fetch_tpex_quotes", fake_tpex)

    result = await rankings.top_losers(limit=1, date=dt.date(2025, 8, 8), market="TPEX")
    assert result["items"][0]["symbol"] == "5483"  # most negative in sample


@pytest.mark.asyncio
async def test_most_actives_all(monkeypatch, mi_payload, tpex_payload):
    async def fake_twse(date: dt.date):
        return mi_payload

    async def fake_tpex(date: dt.date):
        return tpex_payload

    monkeypatch.setattr(rankings, "_fetch_twse_mi_index", fake_twse)
    monkeypatch.setattr(rankings, "_fetch_tpex_quotes", fake_tpex)

    result = await rankings.most_actives(limit=2, date=dt.date(2025, 8, 8), market="ALL")
    assert result["items"][0]["symbol"] == "5490"
    assert result["items"][0]["market"] == "TPEX"



@pytest.mark.asyncio
async def test_top_gainers(monkeypatch, mi_payload):
    async def fake_fetch(date: dt.date):
        return mi_payload

    monkeypatch.setattr(rankings, "_fetch_twse_mi_index", fake_fetch)

    result = await rankings.top_gainers(limit=2, date=dt.date(2025, 8, 8))
    codes = [it["symbol"] for it in result["items"]]
    assert codes[0] == "2603"  # highest +%
    assert len(codes) == 2


@pytest.mark.asyncio
async def test_top_losers(monkeypatch, mi_payload):
    async def fake_fetch(date: dt.date):
        return mi_payload

    monkeypatch.setattr(rankings, "_fetch_twse_mi_index", fake_fetch)

    result = await rankings.top_losers(limit=1, date=dt.date(2025, 8, 8))
    codes = [it["symbol"] for it in result["items"]]
    assert codes[0] == "2330"  # most negative %


@pytest.mark.asyncio
async def test_most_actives(monkeypatch, mi_payload):
    async def fake_fetch(date: dt.date):
        return mi_payload

    monkeypatch.setattr(rankings, "_fetch_twse_mi_index", fake_fetch)

    result = await rankings.most_actives(limit=1, date=dt.date(2025, 8, 8))
    codes = [it["symbol"] for it in result["items"]]
    assert codes[0] == "2603"  # largest volume
