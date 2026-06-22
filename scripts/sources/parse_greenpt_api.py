"""
parse_greenpt_api.py — GreenPT AI API ceny

Zdroj (HTML dokumentácia):
  https://docs.greenpt.ai/models

GreenPT je EU provider (Holandsko), 100% zelená energia, GDPR-compliant.
Parsujeme ceny za milión tokenov.
"""
from __future__ import annotations

import re
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sources.shared import get_client, now_iso, emit, eprint

try:
    from bs4 import BeautifulSoup
except ImportError:
    from sources.shared import die
    die("Chýba knižnica: pip install beautifulsoup4")

# ---------------------------------------------------------------------------
# Konfigurácia
# ---------------------------------------------------------------------------

SOURCE_URL = "https://docs.greenpt.ai/models"

TARGET_MODELS = [
    {
        "model_id": "deepseek-v4",
        "model_name": "DeepSeek Pro v4",
        "search_keywords": ["deepseek"],
    },
    {
        "model_id": "glm-5.2",
        "model_name": "GLM 5.2",
        "search_keywords": ["glm"],
    },
    {
        "model_id": "minimax-m3",
        "model_name": "MiniMax M3",
        "search_keywords": ["minimax"],
    },
    {
        "model_id": "qwen-3.6",
        "model_name": "Qwen 3.6",
        "search_keywords": ["qwen3-235", "qwen 3"],
    },
]

# Záložné hodnoty (ceny v EUR)
# Zdroj: https://docs.greenpt.ai/models (overené 2026-06-22)
# GreenPT ponúka predovšetkým Gemma, Llama, Mistral, Qwen modely
FALLBACK_PRICES: dict[str, tuple[float, float] | None] = {
    "deepseek-v4": None,       # nie je dostupný na GreenPT
    "glm-5.2": None,           # nie je dostupný na GreenPT
    "minimax-m3": None,        # nie je dostupný na GreenPT
    "qwen-3.6": (0.90, 0.90),  # Qwen3-235b-instruct (EUR)
}

PRICE_RE = re.compile(r"[€\$]\s*([\d]+[.,][\d]+)")
PRICE_NUM_RE = re.compile(r"([\d]+\.[\d]+)")


def find_prices(text: str) -> tuple[float, float] | None:
    prices = PRICE_RE.findall(text)
    if len(prices) >= 2:
        return (
            float(prices[0].replace(",", ".")),
            float(prices[1].replace(",", ".")),
        )
    if len(prices) == 1:
        # Len jedna cena — input a output rovnaká
        p = float(prices[0].replace(",", "."))
        return (p, p)
    return None


def main() -> None:
    eprint(f"[GreenPT] Sťahujem: {SOURCE_URL}")

    with get_client() as client:
        try:
            r = client.get(SOURCE_URL)
            r.raise_for_status()
        except Exception as exc:
            eprint(f"[GreenPT] Stiahnutie zlyhalo: {exc} — použijem fallback")
            emit({
                "provider_id": "greenpt-api",
                "type": "api",
                "source_url": SOURCE_URL,
                "fetched_at": now_iso(),
                "models": _build_output({}),
                "warning": "Stránka nedostupná",
            })
            return

    soup = BeautifulSoup(r.text, "lxml")
    found: dict[str, tuple[float, float]] = {}

    # Dokumentačná stránka — hľadáme tabuľky a sekcie
    for elem in soup.find_all(["tr", "div", "li", "td", "p", "section"]):
        elem_text = elem.get_text(" ", strip=True)
        elem_lower = elem_text.lower()
        for cfg in TARGET_MODELS:
            if cfg["model_id"] in found:
                continue
            if any(kw.lower() in elem_lower for kw in cfg["search_keywords"]):
                prices = find_prices(elem_text)
                if prices:
                    found[cfg["model_id"]] = prices
                    eprint(
                        f"[GreenPT] {cfg['model_id']}: "
                        f"{prices[0]}/M in, {prices[1]}/M out"
                    )

    emit({
        "provider_id": "greenpt-api",
        "type": "api",
        "source_url": SOURCE_URL,
        "fetched_at": now_iso(),
        "models": _build_output(found),
    })


def _build_output(found: dict) -> list[dict]:
    result = []
    for cfg in TARGET_MODELS:
        mid = cfg["model_id"]
        prices = found.get(mid) or FALLBACK_PRICES.get(mid)
        if prices:
            result.append({
                "model_id": mid,
                "model_name": cfg["model_name"],
                "input_price_per_million_eur": prices[0],
                "output_price_per_million_eur": prices[1],
                "is_available": True,
                "note": "parsovaná zo stránky" if mid in found else "fallback",
            })
        else:
            result.append({
                "model_id": mid,
                "model_name": cfg["model_name"],
                "input_price_per_million_eur": 0,
                "output_price_per_million_eur": 0,
                "is_available": False,
                "note": "nedostupný na GreenPT",
            })
    return result


if __name__ == "__main__":
    main()
