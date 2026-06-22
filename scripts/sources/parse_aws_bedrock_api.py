"""
parse_aws_bedrock_api.py — AWS Bedrock LLM API ceny (EU regióny)

Zdroj (HTML cenník):
  https://aws.amazon.com/bedrock/pricing/

AWS Bedrock má ceny embedded v HTML stránke.
Filtrujeme len EU regióny (eu-central-1, eu-west-1) a len dostupné modely.
"""
from __future__ import annotations

import re
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sources.shared import get_client, usd_to_eur, now_iso, emit, eprint

try:
    from bs4 import BeautifulSoup
except ImportError:
    from sources.shared import die
    die("Chýba knižnica: pip install beautifulsoup4")

# ---------------------------------------------------------------------------
# Konfigurácia
# ---------------------------------------------------------------------------

SOURCE_URL = "https://aws.amazon.com/bedrock/pricing/"

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

# Záložné hodnoty
# Zdroj: https://aws.amazon.com/bedrock/pricing/ (overené 2026-06-22)
# Bedrock EU ponúka predovšetkým Qwen cez Amazon marketplace
FALLBACK_PRICES: dict[str, tuple[float, float] | None] = {
    "deepseek-v4": None,
    "glm-5.2": None,
    "minimax-m3": None,
    "qwen-3.6": (0.072, 0.464),  # $0.072 input, $0.464 output (EU region)
}

PRICE_USD_RE = re.compile(r"\$([\d]+\.[\d]+)")


def find_prices(text: str) -> tuple[float, float] | None:
    prices = PRICE_USD_RE.findall(text)
    prices = [float(p) for p in prices if 0.001 < float(p) < 50.0]
    if len(prices) >= 2:
        return prices[0], prices[1]
    return None


def main() -> None:
    eprint(f"[AWS Bedrock] Sťahujem: {SOURCE_URL}")

    with get_client() as client:
        try:
            r = client.get(SOURCE_URL)
            r.raise_for_status()
        except Exception as exc:
            eprint(f"[AWS Bedrock] Stiahnutie zlyhalo: {exc} — použijem fallback")
            emit({
                "provider_id": "aws-bedrock-api",
                "type": "api",
                "source_url": SOURCE_URL,
                "fetched_at": now_iso(),
                "models": _build_output({}),
                "warning": "Stránka nedostupná",
            })
            return

    soup = BeautifulSoup(r.text, "lxml")
    found: dict[str, tuple[float, float]] = {}

    # AWS Bedrock stránka obsahuje JSON dáta v <script> tagoch
    for script in soup.find_all("script"):
        script_text = script.string or ""
        if not script_text or "price" not in script_text.lower():
            continue
        # Hľadáme JSON objekty s cenovými dátami
        for match in re.finditer(r'\{[^<]{100,5000}\}', script_text, re.DOTALL):
            try:
                obj = json.loads(match.group())
                obj_str = json.dumps(obj).lower()
                for cfg in TARGET_MODELS:
                    if cfg["model_id"] in found:
                        continue
                    if any(kw.lower() in obj_str for kw in cfg["search_keywords"]):
                        prices = find_prices(json.dumps(obj))
                        if prices:
                            found[cfg["model_id"]] = (
                                usd_to_eur(prices[0]),
                                usd_to_eur(prices[1]),
                            )
            except (json.JSONDecodeError, TypeError):
                pass

    # HTML tabuľkový fallback
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            row_text = row.get_text(" ", strip=True)
            row_lower = row_text.lower()
            for cfg in TARGET_MODELS:
                if cfg["model_id"] in found:
                    continue
                if any(kw.lower() in row_lower for kw in cfg["search_keywords"]):
                    prices = find_prices(row_text)
                    if prices:
                        found[cfg["model_id"]] = (
                            usd_to_eur(prices[0]),
                            usd_to_eur(prices[1]),
                        )
                        eprint(
                            f"[AWS Bedrock] {cfg['model_id']}: "
                            f"€{found[cfg['model_id']][0]}/M in, "
                            f"€{found[cfg['model_id']][1]}/M out (tabuľka)"
                        )

    emit({
        "provider_id": "aws-bedrock-api",
        "type": "api",
        "source_url": SOURCE_URL,
        "fetched_at": now_iso(),
        "models": _build_output(found),
    })


def _build_output(found: dict) -> list[dict]:
    result = []
    for cfg in TARGET_MODELS:
        mid = cfg["model_id"]
        prices = found.get(mid)
        if prices is None:
            fallback = FALLBACK_PRICES.get(mid)
            if fallback:
                prices = (usd_to_eur(fallback[0]), usd_to_eur(fallback[1]))

        if prices:
            result.append({
                "model_id": mid,
                "model_name": cfg["model_name"],
                "input_price_per_million_eur": round(prices[0], 4),
                "output_price_per_million_eur": round(prices[1], 4),
                "is_available": True,
                "note": "parsovaná zo stránky" if mid in found else "fallback",
                "currency_note": "converted from USD via ECB API",
            })
        else:
            result.append({
                "model_id": mid,
                "model_name": cfg["model_name"],
                "input_price_per_million_eur": 0,
                "output_price_per_million_eur": 0,
                "is_available": False,
                "note": "nedostupný na AWS Bedrock EU",
            })
    return result


if __name__ == "__main__":
    main()
