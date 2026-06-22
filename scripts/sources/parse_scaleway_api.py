"""
parse_scaleway_api.py — Scaleway AI/LLM API ceny

Zdroj (HTML cenník):
  https://www.scaleway.com/en/pricing/?tags=ai

Parsujeme ceny za milión tokenov pre modely.
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

SOURCE_URL = "https://www.scaleway.com/en/pricing/?tags=ai"

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
        "search_keywords": ["qwen"],
    },
]

# Záložné hodnoty - Scaleway má len Qwen 3.6 (35B)
FALLBACK_PRICES = {
    "qwen-3.6": (0.072, 0.464),
}

PRICE_RE = re.compile(r"\$\s*([\d]+\.[\d]+)")
PRICE_EUR_RE = re.compile(r"€\s*([\d]+[.,][\d]+)")


def extract_prices(text: str) -> tuple[float, float] | None:
    prices = PRICE_RE.findall(text)
    if len(prices) >= 2:
        return float(prices[0]), float(prices[1])
    prices_eur = PRICE_EUR_RE.findall(text)
    if len(prices_eur) >= 2:
        return (
            float(prices_eur[0].replace(",", ".")),
            float(prices_eur[1].replace(",", ".")),
        )
    return None


def main() -> None:
    eprint(f"[Scaleway] Sťahujem: {SOURCE_URL}")

    with get_client() as client:
        try:
            r = client.get(SOURCE_URL)
            r.raise_for_status()
        except Exception as exc:
            eprint(f"[Scaleway] Stiahnutie zlyhalo: {exc} — použijem fallback")
            emit({
                "provider_id": "scaleway",
                "type": "api",
                "source_url": SOURCE_URL,
                "fetched_at": now_iso(),
                "models": _build_output({}),
                "warning": "Stránka nedostupná",
            })
            return

    soup = BeautifulSoup(r.text, "lxml")

    found: dict[str, tuple[float, float]] = {}

    # Scaleway má pricing v JSON vloženom do HTML (Next.js)
    scripts = soup.find_all("script", type="application/json")
    for script in scripts:
        try:
            data = json.loads(script.string or "")
            text = json.dumps(data).lower()
            for cfg in TARGET_MODELS:
                if cfg["model_id"] in found:
                    continue
                if any(kw in text for kw in cfg["search_keywords"]):
                    # Hľadáme ceny v okolí kľúčového slova
                    prices = extract_prices(json.dumps(data))
                    if prices:
                        found[cfg["model_id"]] = prices
        except (json.JSONDecodeError, TypeError):
            pass

    # Fallback: prehľadáme HTML text
    if not found:
        rows = soup.find_all(["tr", "div", "li"])
        for row in rows:
            row_text = row.get_text(" ", strip=True)
            row_lower = row_text.lower()
            for cfg in TARGET_MODELS:
                if cfg["model_id"] in found:
                    continue
                if any(kw in row_lower for kw in cfg["search_keywords"]):
                    prices = extract_prices(row_text)
                    if prices:
                        found[cfg["model_id"]] = prices
                        eprint(
                            f"[Scaleway] {cfg['model_id']}: "
                            f"${prices[0]}/M in, ${prices[1]}/M out"
                        )

    emit({
        "provider_id": "scaleway",
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
                "note": "parsovaná" if mid in found else "fallback",
            })
        else:
            result.append({
                "model_id": mid,
                "model_name": cfg["model_name"],
                "input_price_per_million_eur": 0,
                "output_price_per_million_eur": 0,
                "is_available": False,
                "note": "nedostupný na Scaleway",
            })
    return result


if __name__ == "__main__":
    main()
