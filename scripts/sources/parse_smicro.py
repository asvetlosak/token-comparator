"""
parse_smicro.py — SMicro.sk hardware ceny (vlastná infraštruktúra)

Zdroj (HTML - WooCommerce eshop):
  https://smicro.sk/serverove-gpu-1?&pageSizeProducts=48

Parsujeme produktové karty: názov a cenu DGX/GPU serverov.
Ceny sú v EUR (SK predajca).
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

SOURCE_URLS = [
    "https://smicro.sk/dgx-series-2?&pageSizeProducts=48",
    "https://smicro.sk/vyhladavanie?search=H100"
]
USER_FACING_URL = "https://smicro.sk/vyhladavanie?search=H100"

# Poznámka: /serverove-gpu-1 obsahuje jednotlivé GPU karty
# DGX/HGX servery sú na /dgx-series-2

# Produkty ktoré hľadáme — kľúčové slová v názve produktu
TARGET_PRODUCTS: list[dict] = [
    {
        "id": "smicro-dgx-h200",
        "search_keywords": ["h200"],
        "name_override": "NVIDIA DGX H200 8x 141GB",
        "gpu_type": "H200",
        "gpu_count": 8,
        "vram_per_gpu": 141,
        "tflops_fp8": 31824,
    },
    {
        "id": "smicro-dgx-b200",
        "search_keywords": ["b200"],
        "name_override": "NVIDIA DGX B200 8x 180GB",
        "gpu_type": "H200",  # B200 mapujeme na H200 kategóriu
        "gpu_count": 8,
        "vram_per_gpu": 180,
        "tflops_fp8": 72000,
    },
    {
        "id": "smicro-hgx-h100",
        "search_keywords": ["h100", "251 914"],  # HGX cena (v eur bez dph, hack na presný server v search)
        "name_override": "Server 8x H100 80GB",
        "gpu_type": "H100",
        "gpu_count": 8,
        "vram_per_gpu": 80,
        "tflops_fp8": 31824,
    },
    {
        "id": "smicro-h100-pcie",
        "search_keywords": ["27 626"],  # H100 PCIe cena (hack na presnú kartu v search)
        "name_override": "NVIDIA H100 80GB PCIe",
        "gpu_type": "H100",
        "gpu_count": 1,
        "vram_per_gpu": 80,
        "tflops_fp8": 3026,
    },
]

# Záložné ceny (posledné overené hodnoty zo smicro.sk/dgx-series-2)
# Dátum overenia: 2026-06-22
# Ceny bez DPH, EUR
FALLBACK_PRICES_EUR = {
    "smicro-dgx-h200": 398491,
    "smicro-dgx-b200": 380022,
    "smicro-hgx-h100": 251914,
    "smicro-h100-pcie": 27626,
}

PRICE_RE = re.compile(r"([\d\s]+[,.][\d]+)\s*€")
PRICE_RE2 = re.compile(r"€\s*([\d\s]+[,.][\d]+)")


def clean_price(text: str) -> float | None:
    """Extrahuje cenu bez DPH z textu napr. '€ 35 472,75 bez DPH' → 35472.75"""
    # Hladame vzor: euro + cislo + 'bez DPH'
    # Formaty: '€ 35 472,75bez DPH', '€430 368,67bez DPH'
    bez_dph = re.search(
        r'€\s*([\d\s\xa0]+[,.]\d{2})\s*bez\s*DPH',
        text, re.IGNORECASE
    )
    if bez_dph:
        raw = bez_dph.group(1).replace('\xa0', '').replace(' ', '').replace(',', '.')
        try:
            return float(raw)
        except ValueError:
            pass
    # Fallback: akakolvek EUR cena
    for pattern in [PRICE_RE, PRICE_RE2]:
        m = pattern.search(text)
        if m:
            raw = m.group(1).replace(' ', '').replace('\xa0', '').replace(',', '.')
            try:
                return float(raw)
            except ValueError:
                pass
    return None


def main() -> None:
    product_cards = []
    
    with get_client() as client:
        for url in SOURCE_URLS:
            eprint(f"[SMicro] Sťahujem: {url}")
            try:
                r = client.get(url)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "lxml")
                product_cards.extend(soup.find_all(class_="item"))
            except Exception as exc:
                eprint(f"[SMicro] Stiahnutie zlyhalo pre {url}: {exc}")

    if not product_cards:
        eprint("[SMicro] Žiadne produktové karty nenájdené — použijem fallback")
        emit({
            "provider_id": "on-premise",
            "type": "hardware",
            "source_url": USER_FACING_URL,
            "fetched_at": now_iso(),
            "instances": [
                {
                    **{k: v for k, v in prod.items() if k != "search_keywords"},
                    "hardware_cost_eur": FALLBACK_PRICES_EUR.get(prod["id"]),
                    "note": "fallback — stránka nedostupná",
                }
                for prod in TARGET_PRODUCTS
                if FALLBACK_PRICES_EUR.get(prod["id"]) is not None
            ],
            "warning": "Použité fallback hodnoty",
        })
        return

    eprint(f"[SMicro] Celkovo nájdených {len(product_cards)} produktových kariet (.item)")

    instances_out = []

    for prod_cfg in TARGET_PRODUCTS:
        keywords = prod_cfg["search_keywords"]
        found_price = None
        found_name = None

        found_url = None
        for card in product_cards:
            card_text = card.get_text(" ", strip=True)
            card_lower = card_text.lower()
            if all(kw.lower() in card_lower for kw in keywords):
                found_name = card_text[:80]
                # Cena je v .itemPrice elemente
                price_el = card.find(class_="itemPrice")
                price_text = price_el.get_text(" ", strip=True) if price_el else card_text
                found_price = clean_price(price_text)
                if found_price:
                    a_tag = card.find("a")
                    href = a_tag["href"] if a_tag and "href" in a_tag.attrs else ""
                    if href and not href.startswith("http"):
                        href = "https://smicro.sk" + href
                    found_url = href
                    eprint(
                        f"[SMicro] Nájdený '{prod_cfg['id']}': "
                        f"{found_price:,.0f} EUR (bez DPH)"
                    )
                    break

        if found_price is None:
            fallback = FALLBACK_PRICES_EUR.get(prod_cfg["id"])
            if fallback is None:
                continue
            eprint(
                f"[SMicro] '{prod_cfg['id']}' nenájdený na stránke — "
                "použijem fallback"
            )
            found_price = fallback
            found_url = ""
            note = "fallback — produkt nenájdený na stránke"
        else:
            note = "parsovaná zo stránky (bez DPH)"

        instances_out.append(
            {
                "id": prod_cfg["id"],
                "name": prod_cfg["name_override"],
                "gpu_type": prod_cfg["gpu_type"],
                "gpu_count": prod_cfg["gpu_count"],
                "vram_per_gpu": prod_cfg["vram_per_gpu"],
                "hardware_cost_eur": round(found_price, 2),
                "item_url": found_url or "",
                "note": note,
            }
        )

    emit(
        {
            "provider_id": "on-premise",
            "type": "hardware",
            "source_url": USER_FACING_URL,
            "fetched_at": now_iso(),
            "instances": instances_out,
        }
    )


if __name__ == "__main__":
    main()
