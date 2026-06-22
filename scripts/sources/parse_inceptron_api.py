"""
parse_inceptron_api.py — Inceptron AI API ceny

Zdroj (HTML stránka modelov):
  https://www.inceptron.io/models

Inceptron je EU provider (Švédsko), ponúka serverless a dedikované GPU.
Parsujeme ceny za milión tokenov pre dostupné modely.
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

SOURCE_URL = "https://www.inceptron.io/models"

TARGET_MODELS = [
    {
        "model_id": "deepseek-v4",
        "model_name": "DeepSeek Pro v4",
        "search_keywords": ["deepseek-v4", "deepseek v4", "deepseek pro"],
    },
    {
        "model_id": "glm-5.2",
        "model_name": "GLM 5.2",
        "search_keywords": ["glm-5.2", "glm 5.2"],
    },
    {
        "model_id": "minimax-m3",
        "model_name": "MiniMax M3",
        "search_keywords": ["minimax-m3", "minimax m3"],
    },
    {
        "model_id": "qwen-3.6",
        "model_name": "Qwen 3.6",
        "search_keywords": ["qwen3", "qwen 3.6"],
    },
]

# Záložné hodnoty
# Zdroj: https://www.inceptron.io/models (overené 2026-06-22)
# Inceptron aktuálne ponúka predovšetkým MiniMax modely
FALLBACK_PRICES: dict[str, tuple[float, float] | None] = {
    "deepseek-v4": None,
    "glm-5.2": None,
    "minimax-m3": None,     # ak bude dostupný, doplniť
    "qwen-3.6": None,
}

PRICE_USD_RE = re.compile(r"\$\s*([\d]+\.[\d]+)")
PRICE_EUR_RE = re.compile(r"€\s*([\d]+[.,][\d]+)")


def find_prices(text: str) -> tuple[float, float] | None:
    prices = PRICE_USD_RE.findall(text) or PRICE_EUR_RE.findall(text)
    if len(prices) >= 2:
        return float(prices[0].replace(",", ".")), float(prices[1].replace(",", "."))
    return None


def main() -> None:
    eprint(f"[Inceptron] Sťahujem: {SOURCE_URL}")

    with get_client() as client:
        try:
            r = client.get(SOURCE_URL)
            r.raise_for_status()
        except Exception as exc:
            eprint(f"[Inceptron] Stiahnutie zlyhalo: {exc} — použijem fallback")
            emit({
                "provider_id": "inceptron-api",
                "type": "api",
                "source_url": SOURCE_URL,
                "fetched_at": now_iso(),
                "models": _build_output({}),
                "warning": "Stránka nedostupná",
            })
            return

    soup = BeautifulSoup(r.text, "lxml")
    found: dict[str, tuple[float, float]] = {}

    # Inceptron môže mať JSON dáta v skriptoch (Next.js)
    for script in soup.find_all("script"):
        script_text = script.string or ""
        if "price" not in script_text.lower():
            continue
        try:
            # Hľadáme JSON objekty
            for match in re.finditer(r'\{[^{}]{50,}\}', script_text):
                try:
                    obj = json.loads(match.group())
                    obj_text = json.dumps(obj).lower()
                    for cfg in TARGET_MODELS:
                        if cfg["model_id"] in found:
                            continue
                        if any(kw.lower() in obj_text for kw in cfg["search_keywords"]):
                            prices = find_prices(json.dumps(obj))
                            if prices:
                                found[cfg["model_id"]] = prices
                except (json.JSONDecodeError, TypeError):
                    pass
        except Exception:
            pass

    # HTML fallback
    for elem in soup.find_all(["tr", "div", "li", "article", "section", "card"]):
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
                        f"[Inceptron] {cfg['model_id']}: "
                        f"${prices[0]}/M in, ${prices[1]}/M out"
                    )

    if not found:
        eprint("[Inceptron] Žiadne ceny nenájdené — stránka pravdepodobne JS-renderovaná")

    emit({
        "provider_id": "inceptron-api",
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
                "note": "nedostupný na Inceptron",
            })
    return result


if __name__ == "__main__":
    main()
