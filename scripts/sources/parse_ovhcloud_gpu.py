"""
parse_ovhcloud_gpu.py — OVHcloud GPU inštancie v EU

Zdroj (HTML stránka s cenami):
  https://www.ovhcloud.com/en/public-cloud/gpu/h100/

OVH verejný katalóg API neobsahuje GPU inštancie — tie sú dostupné len cez
dedikované stránky alebo prihlásený účet.

Scrape-ujeme HTML stránku s cenami H100 GPU v EU regiónoch.
Ceny sú v EUR.

Cieľová URL pre používateľa:
  https://www.ovhcloud.com/en/public-cloud/prices/#14
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

# Stránka s cenami H100 v EU
H100_PAGE = "https://www.ovhcloud.com/en/public-cloud/prices/#397"
USER_FACING_URL = H100_PAGE

# Záložné hodnoty (overené 2026-06-22)
# OVH H100 SXM: 8x H100 node ~ 26.24 EUR/hod
FALLBACK: list[dict] = [
    {
        "id": "ovh-h100-8x",
        "name": "8x H100 SXM (OVH Public Cloud GRA)",
        "gpu_type": "H100",
        "gpu_count": 8,
        "vram_per_gpu": 80,
        "price_per_hour_eur": 26.24,
        "note": "fallback — cena z verejného cenníka OVH",
    },
]

def main() -> None:
    eprint(f"[OVH] Sťahujem: {H100_PAGE}")

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
    with get_client() as client:
        try:
            r = client.get(H100_PAGE, headers=headers)
            r.raise_for_status()
        except Exception as exc:
            eprint(f"[OVH] Stiahnutie zlyhalo: {exc} — použijem fallback")
            emit({
                "provider_id": "ovhcloud",
                "type": "gpu",
                "source_url": USER_FACING_URL,
                "fetched_at": now_iso(),
                "instances": FALLBACK,
                "warning": "Stránka nedostupná — použité fallback hodnoty",
            })
            return

    soup = BeautifulSoup(r.text, "lxml")
    instances_out: list[dict] = []

    # Hľadáme atribút data-price s JSON na základe planCode
    # OVH má h100-380 (1x), h100-760 (2x), h100-1520 (4x)
    target_tag = soup.find(lambda tag: tag.has_attr('data-plancode') and tag['data-plancode'] == 'h100-1520.consumption')
    
    found_price_eur = None
    if target_tag and target_tag.has_attr('data-price'):
        try:
            price_data = json.loads(target_tag['data-price'])
            gra = price_data.get("GRA", {})
            hourly = gra.get("linux.hourly", "")
            m = re.search(r'\$\s*([0-9.,]+)', hourly)
            if m:
                price_usd = float(m.group(1).replace(',', ''))
                # h100-1520 sú 4 karty, potrebujeme 8x -> * 2.0
                total_usd = price_usd * 2.0
                found_price_eur = usd_to_eur(total_usd)
                
                eprint(f"[OVH] Nájdená cena pre 4x H100 (usd): ${price_usd:.2f}, 8x = ${total_usd:.2f} -> {found_price_eur:.2f} EUR")
        except Exception as e:
            eprint(f"[OVH] Chyba pri parsovaní ceny: {e}")

    if found_price_eur:
        instances_out.append({
            "id": "ovh-h100-8x",
            "name": "8x H100 SXM (OVH Public Cloud GRA)",
            "gpu_type": "H100",
            "gpu_count": 8,
            "vram_per_gpu": 80,
            "price_per_hour_eur": round(found_price_eur, 4),
            "note": "parsovaná z HTML (h100-1520.consumption * 2, USD->EUR)",
        })
    else:
        eprint("[OVH] Ceny nenájdené v HTML — použijem fallback")
        instances_out = FALLBACK

    emit({
        "provider_id": "ovhcloud",
        "type": "gpu",
        "source_url": USER_FACING_URL,
        "pricing_page_url": H100_PAGE,
        "fetched_at": now_iso(),
        "instances": instances_out,
    })


if __name__ == "__main__":
    main()
