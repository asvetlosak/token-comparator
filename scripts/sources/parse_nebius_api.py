"""
parse_nebius_api.py — Nebius AI Token Factory API ceny

Zdroj (interné JSON API pre tokenfactory.nebius.com):
  https://tokenfactory.nebius.com/proxy/inference/private/v1/models_info

Parsujeme ceny za milión tokenov priamo z JSON odpovede.
Hľadáme modely: DeepSeek Pro v4, GLM 5.2, MiniMax M3, Qwen 3.6
"""
from __future__ import annotations

import re
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sources.shared import get_client, usd_to_eur, now_iso, emit, eprint

# ---------------------------------------------------------------------------
# Konfigurácia
# ---------------------------------------------------------------------------

SOURCE_URL = "https://tokenfactory.nebius.com/proxy/inference/private/v1/models_info"
USER_FACING_URL = "https://tokenfactory.nebius.com/models"

TARGET_MODELS = [
    {
        "model_id": "deepseek-v4",
        "model_name": "DeepSeek Pro v4",
        "search_keywords": ["deepseek", "v4"],
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
        "search_keywords": ["qwen", "3.6"],
    },
]


def main() -> None:
    eprint(f"[Nebius API] Sťahujem: {SOURCE_URL}")

    with get_client() as client:
        try:
            r = client.get(SOURCE_URL)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            eprint(f"[Nebius API] Zlyhanie: {exc}")
            return

    models_out = []
    
    # Skúsime nájsť dáta v odpovedi (môže to byť priamo list objektov)
    if isinstance(data, list):
        api_models = data
    else:
        api_models = data.get("models", [])

    for model_cfg in TARGET_MODELS:
        model_id = model_cfg["model_id"]
        keywords = model_cfg["search_keywords"]
        found_prices = None

        for am in api_models:
            name = am.get("name", "").lower()
            if all(kw in name for kw in keywords):
                # JSON od nebius obsahuje 'flavors' pole s cenami v USD
                flavors = am.get("flavors", [])
                if flavors:
                    f = flavors[0]
                    inp = f.get("input_price_per_million_tokens")
                    out = f.get("output_price_per_million_tokens")
                    if inp is not None and out is not None:
                        found_prices = (float(inp), float(out))
                        break

        if found_prices is None:
            eprint(f"[Nebius API] {model_id} nenájdený v odpovedi")
            models_out.append({
                "model_id": model_id,
                "model_name": model_cfg["model_name"],
                "input_price_per_million_eur": 0,
                "output_price_per_million_eur": 0,
                "is_available": False,
                "note": "model nenájdený v API",
            })
        else:
            inp_usd, out_usd = found_prices
            inp_eur = usd_to_eur(inp_usd)
            out_eur = usd_to_eur(out_usd)
            
            eprint(
                f"[Nebius API] {model_id}: "
                f"IN ${inp_usd:.2f} -> {inp_eur:.2f} EUR, "
                f"OUT ${out_usd:.2f} -> {out_eur:.2f} EUR"
            )
            models_out.append({
                "model_id": model_id,
                "model_name": model_cfg["model_name"],
                "input_price_per_million_eur": inp_eur,
                "output_price_per_million_eur": out_eur,
                "is_available": True,
                "note": "parsované z private API (USD->EUR)",
            })

    emit({
        "provider_id": "nebius-api",
        "type": "api",
        "source_url": USER_FACING_URL,
        "pricing_api_url": SOURCE_URL,
        "fetched_at": now_iso(),
        "models": models_out,
    })


if __name__ == "__main__":
    main()
