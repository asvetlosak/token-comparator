"""
parse_azure_gpu.py — Azure VM GPU ceny pre EU regióny

Zdroj (machine-readable REST API):
  https://prices.azure.com/api/retail/prices

Cieľová URL pre používateľa (cenník pre konkrétnu sériu):
  https://azure.microsoft.com/en-us/pricing/details/virtual-machines/linux/#nd-h100-v5-series

Filtrujeme: ND H100 v5 séria, West Europe / North Europe, Linux, OnDemand (nie spot, nie rezervácie).
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sources.shared import get_client, usd_to_eur, now_iso, emit, eprint, die

# ---------------------------------------------------------------------------
# Konfigurácia
# ---------------------------------------------------------------------------

AZURE_PRICES_API = "https://prices.azure.com/api/retail/prices"

# Priamy odkaz na pricing page pre ND H100 v5 sériu v EU
USER_FACING_URL = (
    "https://azure.microsoft.com/en-us/pricing/details/virtual-machines/linux/"
    "#nd-h100-v5-series"
)

# OData filtre pre Azure Retail API
# armSkuName pre ND H100 v5: Standard_ND96isr_H100_v5
QUERIES = [
    {
        "filter": (
            "armSkuName eq 'Standard_ND96isr_H100_v5' "
            "and priceType eq 'Consumption' "
            "and (armRegionName eq 'westeurope' or armRegionName eq 'northeurope')"
        ),
        "gpu_type": "H100",
        "gpu_count": 8,
        "vram_per_gpu": 80,
        "instance_base_id": "az-nd96isr",
        "instance_name": "ND96isr_H100_v5 (8x H100 SXM)",
    },
]

EU_REGIONS = {"westeurope": "EU (West Europe)", "northeurope": "EU (North Europe)"}


def fetch_prices(client, query_cfg: dict) -> list[dict]:
    params = {
        "$filter": query_cfg["filter"],
        "api-version": "2023-01-01-preview",
    }
    eprint(f"[Azure] Sťahujem: {AZURE_PRICES_API} filter={query_cfg['filter'][:60]}...")
    try:
        r = client.get(AZURE_PRICES_API, params=params)
        r.raise_for_status()
    except Exception as exc:
        die(f"Azure: stiahnutie zlyhalo — {exc}")

    items = r.json().get("Items", [])
    results = []
    seen_regions: set[str] = set()

    for item in items:
        region = item.get("armRegionName", "")
        if region not in EU_REGIONS:
            continue
        if region in seen_regions:
            continue
        # Preskočíme Spot / Low Priority / rezervácie
        sku_name = item.get("skuName", "")
        if "Spot" in sku_name or "Low" in sku_name:
            continue
        price_usd = float(item.get("retailPrice", 0))
        if price_usd <= 0:
            continue

        seen_regions.add(region)
        price_eur = usd_to_eur(price_usd)
        eprint(
            f"[Azure] {item.get('skuName')} @ {region}: "
            f"${price_usd:.4f}/hod → {price_eur:.4f} EUR/hod"
        )
        results.append(
            {
                "id": f"{query_cfg['instance_base_id']}-{region}",
                "name": f"{query_cfg['instance_name']} ({EU_REGIONS[region]})",
                "gpu_type": query_cfg["gpu_type"],
                "gpu_count": query_cfg["gpu_count"],
                "vram_per_gpu": query_cfg["vram_per_gpu"],
                "region": region,
                "price_per_hour_usd": price_usd,
                "price_per_hour_eur": price_eur,
                "currency_note": "converted from USD via ECB API",
                "sku_name": item.get("skuName"),
            }
        )

    return results


def main() -> None:
    all_instances = []

    with get_client() as client:
        for q in QUERIES:
            all_instances.extend(fetch_prices(client, q))

    if not all_instances:
        die("Žiadne Azure inštancie nenájdené — skontroluj filter alebo región")

    emit(
        {
            "provider_id": "azure",
            "type": "gpu",
            "source_url": USER_FACING_URL,
            "pricing_api_url": AZURE_PRICES_API,
            "fetched_at": now_iso(),
            "instances": all_instances,
        }
    )


if __name__ == "__main__":
    main()
