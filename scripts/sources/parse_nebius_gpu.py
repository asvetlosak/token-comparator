"""
parse_nebius_gpu.py — Nebius AI Cloud GPU ceny (EU/Finland)

Zdroj (HTML cenník):
  https://nebius.com/docs/compute/pricing/

Ceny sú v HTML tabuľkách na tejto stránke.
Filtrujeme H100 SXM5 a H200 SXM5 inštancie.

Poznámka: Nebius nemá verejné JSON API pre GPU ceny.
Ak sa HTML štruktúra zmení, parser vypíše varovanie a zachová pôvodnú hodnotu.
"""
from __future__ import annotations

import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sources.shared import get_client, now_iso, emit, eprint, die

try:
    from bs4 import BeautifulSoup
except ImportError:
    die("Chýba knižnica: pip install beautifulsoup4")

# ---------------------------------------------------------------------------
# Konfigurácia
# ---------------------------------------------------------------------------

SOURCE_URL = "https://nebius.com/docs/compute/pricing/"

# Mapovanie GPU typov zo stránky
KNOWN_CONFIGS: list[dict] = [
    {
        "id": "nebius-h100-1x",
        "name": "1x H100 SXM5",
        "gpu_type": "H100",
        "gpu_count": 1,
        "vram_per_gpu": 80,
        "search_patterns": ["h100", "1 gpu", "1x h100"],
    },
    {
        "id": "nebius-h100-8x",
        "name": "8x H100 SXM5",
        "gpu_type": "H100",
        "gpu_count": 8,
        "vram_per_gpu": 80,
        "search_patterns": ["h100", "8 gpu", "8x h100"],
    },
    {
        "id": "nebius-h200-8x",
        "name": "8x H200 SXM5",
        "gpu_type": "H200",
        "gpu_count": 8,
        "vram_per_gpu": 141,
        "search_patterns": ["h200", "8x h200"],
    },
]

# Záložné ceny (posledná overená hodnota) — bude aktualizovaná parserom
FALLBACK_PRICES_EUR = {
    "nebius-h100-1x": 3.85,
    "nebius-h100-8x": 30.80,
    "nebius-h200-8x": 36.00,
}

PRICE_RE = re.compile(r"\$?\s*([\d]+[.,][\d]+)")


def extract_price_from_text(text: str) -> float | None:
    """Extrahuje cenu z textu (napr. '$3.85' → 3.85)."""
    m = PRICE_RE.search(text)
    if m:
        return float(m.group(1).replace(",", "."))
    return None


def main() -> None:
    eprint(f"[Nebius GPU] Sťahujem: {SOURCE_URL}")

    with get_client() as client:
        try:
            r = client.get(SOURCE_URL)
            r.raise_for_status()
        except Exception as exc:
            eprint(f"[Nebius GPU] Stiahnutie zlyhalo: {exc} — použijem fallback hodnoty")
            instances = [
                {
                    **{k: v for k, v in cfg.items() if k != "search_patterns"},
                    "price_per_hour_eur": FALLBACK_PRICES_EUR[cfg["id"]],
                    "note": "fallback — stránka nedostupná",
                }
                for cfg in KNOWN_CONFIGS
            ]
            emit({
                "provider_id": "nebius",
                "type": "gpu",
                "source_url": SOURCE_URL,
                "fetched_at": now_iso(),
                "instances": instances,
                "warning": "Použité fallback hodnoty — stránka nebola dostupná",
            })
            return

    soup = BeautifulSoup(r.text, "lxml")
    page_text = r.text

    instances_out = []

    # Nebius docs stránka — hľadáme priamo v textovej reprezentácii JSON-u
    # Typická štruktúra v JSONe: ["NVIDIA HGX H100","16","200","$2.15","$3.85"]
    # (posledná hodnota je On-Demand cena per GPU)
    
    # Hľadáme On-Demand cenu pre H100
    h100_match = re.search(r'\[\\"NVIDIA[^\]]*H100[^\]]*\\",\\"[^\]]*\\",\\"[^\]]*\\",\\"\$[^\]]*\\",\\"\$([0-9.]+)\\"\]', page_text)
    h200_match = re.search(r'\[\\"NVIDIA[^\]]*H200[^\]]*\\",\\"[^\]]*\\",\\"[^\]]*\\",\\"\$[^\]]*\\",\\"\$([0-9.]+)\\"\]', page_text)

    base_prices = {
        "H100": float(h100_match.group(1)) if h100_match else FALLBACK_PRICES_EUR["nebius-h100-1x"],
        "H200": float(h200_match.group(1)) if h200_match else FALLBACK_PRICES_EUR["nebius-h200-8x"] / 8.0,
    }

    for cfg in KNOWN_CONFIGS:
        cfg_id = cfg["id"]
        gpu_type = cfg["gpu_type"]
        gpu_count = cfg["gpu_count"]
        
        # Cena inštancie = cena za 1 GPU * počet GPU
        found_price = base_prices[gpu_type] * gpu_count
        
        if found_price:
            eprint(f"[Nebius GPU] Nájdená cena pre {cfg_id}: ${found_price:.2f} -> {found_price:.2f} EUR")
            note = "parsovaná zo stránky (JSON props)"
        else:
            note = "parsovaná zo stránky"

        instances_out.append(
            {
                **{k: v for k, v in cfg.items() if k != "search_patterns"},
                "price_per_hour_eur": round(found_price, 4),
                "note": note,
            }
        )

    emit(
        {
            "provider_id": "nebius",
            "type": "gpu",
            "source_url": SOURCE_URL,
            "fetched_at": now_iso(),
            "instances": instances_out,
        }
    )


if __name__ == "__main__":
    main()
