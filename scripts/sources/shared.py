"""
shared.py — Spoločné utility pre všetky parsery

Obsahuje:
- ECB kurz EUR/USD
- HTTP client s timeoutom a User-Agent
- Výstupný formát (stdout JSON)
- Logovanie chýb na stderr
"""
from __future__ import annotations

import json
import sys
import re
from datetime import datetime, timezone
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; token-comparator-pricer/1.0; "
        "+https://github.com/asvetlosak/token-comparator)"
    ),
    "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

TIMEOUT = httpx.Timeout(30.0)


def get_client() -> httpx.Client:
    return httpx.Client(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True)


# ---------------------------------------------------------------------------
# ECB EUR/USD exchange rate
# ---------------------------------------------------------------------------

_ECB_API = (
    "https://data-api.ecb.europa.eu/service/data/EXR/"
    "D.USD.EUR.SP00.A?format=jsondata&lastNObservations=1"
)

_cached_rate: float | None = None


def get_eur_per_usd() -> float:
    """
    Vráti aktuálny kurz: koľko EUR je 1 USD.
    Zdroj: ECB Statistical Data Warehouse API
    https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A
    """
    global _cached_rate
    if _cached_rate is not None:
        return _cached_rate

    try:
        with get_client() as client:
            r = client.get(_ECB_API)
            r.raise_for_status()
            data = r.json()
            # ECB vracia inverzný kurz: USD/EUR = počet USD za 1 EUR
        # Cesta: dataSets[0].series["0:0:0:0:0"].observations
        series = data["dataSets"][0]["series"]
        obs = next(iter(series.values()))["observations"]
        # Posledné pozorovanie = kurz USD/EUR (koľko USD za 1 EUR)
        usd_per_eur = float(next(iter(obs.values()))[0])
        _cached_rate = 1.0 / usd_per_eur  # EUR za 1 USD
        eprint(f"[ECB] 1 USD = {_cached_rate:.4f} EUR (kurz zo {datetime.now(timezone.utc).date()})")
        return _cached_rate
    except Exception as exc:
        eprint(f"[ECB] Kurz sa nepodarilo stiahnuť: {exc}. Použijem fallback 0.93.")
        _cached_rate = 0.93
        return _cached_rate


def usd_to_eur(usd: float) -> float:
    return round(usd * get_eur_per_usd(), 4)


# ---------------------------------------------------------------------------
# Výstup
# ---------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def emit(data: dict[str, Any]) -> None:
    """Vypíše JSON na stdout — tento výstup čítá update_constants.py."""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def eprint(*args: Any) -> None:
    """Vypíše na stderr (nezobrazí sa v JSON pipeline)."""
    print(*args, file=sys.stderr)


def die(msg: str) -> None:
    eprint(f"[ERROR] {msg}")
    sys.exit(1)
