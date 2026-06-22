"""
parse_scaleway_gpu.py — Scaleway GPU inštancie v EU

Zdroj (HTML stránka s cenami):
  https://www.scaleway.com/en/pricing/gpu/?zone=fr-par-2
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

SCALEWAY_URL = "https://www.scaleway.com/en/pricing/gpu/?zone=fr-par-2"

FALLBACK: list[dict] = [
    {
        "id": "scaleway-h100-8x",
        "name": "8x H100 SXM (Scaleway fr-par-2)",
        "gpu_type": "H100",
        "gpu_count": 8,
        "vram_per_gpu": 80,
        "price_per_hour_eur": 25.3308,
        "note": "fallback — cena z verejného cenníka Scaleway",
    },
]

def main() -> None:
    eprint(f"[Scaleway GPU] Sťahujem: {SCALEWAY_URL}")

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
    with get_client() as client:
        try:
            r = client.get(SCALEWAY_URL, headers=headers)
            r.raise_for_status()
        except Exception as exc:
            eprint(f"[Scaleway GPU] Stiahnutie zlyhalo: {exc} — použijem fallback")
            emit({
                "provider_id": "scaleway",
                "type": "gpu",
                "source_url": SCALEWAY_URL,
                "fetched_at": now_iso(),
                "instances": FALLBACK,
                "warning": "Stránka nedostupná — použité fallback hodnoty",
            })
            return

    instances_out: list[dict] = []
    
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', r.text)
    if m:
        try:
            data = json.loads(m.group(1))
            
            def search(obj):
                if isinstance(obj, dict):
                    if obj.get('apiId') == 'H100-SXM-8-80G':
                        zones = obj.get('zones', [])
                        if zones:
                            price_obj = zones[0].get('price', {}).get('hourly', {}).get('value', {})
                            units = price_obj.get('units', 0)
                            nanos = price_obj.get('nanos', 0)
                            eur_price = units + (nanos / 1_000_000_000.0)
                            
                            eprint(f"[Scaleway GPU] Nájdená cena pre H100-SXM-8-80G: {eur_price} EUR/hod")
                            instances_out.append({
                                "id": "scaleway-h100-8x",
                                "name": "8x H100 SXM (Scaleway fr-par-2)",
                                "gpu_type": "H100",
                                "gpu_count": 8,
                                "vram_per_gpu": 80,
                                "price_per_hour_eur": round(eur_price, 4),
                                "note": "parsované z __NEXT_DATA__",
                            })
                        return True
                    for k, v in obj.items():
                        if search(v): return True
                elif isinstance(obj, list):
                    for i in obj:
                        if search(i): return True
                return False
                
            search(data)
        except Exception as e:
            eprint(f"[Scaleway GPU] Chyba pri parsovaní JSON: {e}")

    if not instances_out:
        eprint("[Scaleway GPU] Ceny nenájdené v HTML — použijem fallback")
        instances_out = FALLBACK

    emit({
        "provider_id": "scaleway",
        "type": "gpu",
        "source_url": SCALEWAY_URL,
        "pricing_page_url": SCALEWAY_URL,
        "fetched_at": now_iso(),
        "instances": instances_out,
    })

if __name__ == "__main__":
    main()
