"""
parse_lambda_gpu.py — Lambda Labs GPU ceny (EU/Germany)

Zdroj (public API):
  https://cloud.lambdalabs.com/api/v1/instance-types

  Lambda Labs má verejné REST API (nevyžaduje autentifikáciu pre GET instance-types).
  Dokumentácia: https://docs.lambdalabs.com/public-cloud/cloud-api/

Cieľová URL pre používateľa:
  https://lambdalabs.com/service/gpu-cloud#pricing

Filtrujeme EU regióny (europe-central-1 = Frankfurt, DE).
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sources.shared import get_client, usd_to_eur, now_iso, emit, eprint, die

# ---------------------------------------------------------------------------
# Konfigurácia
# ---------------------------------------------------------------------------

API_URL = "https://cloud.lambdalabs.com/api/v1/instance-types"
USER_FACING_URL = "https://lambdalabs.com/service/gpu-cloud#pricing"

# Lambda Labs EU regióny
EU_REGIONS = {"europe-central-1"}

# Mapovanie Lambda GPU typov na naše interné typy
GPU_TYPE_MAP: dict[str, str] = {
    "H100": "H100",
    "H200": "H200",
    "A100": "H100",   # Ignorujeme — chceme len H100/H200
}

TARGET_GPU_TYPES = {"h100", "h200"}

# Záložné hodnoty (posledná overená cena)
FALLBACK: list[dict] = [
    {
        "id": "lam-h100-1x",
        "name": "1x H100 SXM5 (europe-central-1)",
        "gpu_type": "H100",
        "gpu_count": 1,
        "vram_per_gpu": 80,
        "price_per_hour_eur": 3.29,
        "note": "fallback — API nedostupné",
    },
    {
        "id": "lam-h100-8x",
        "name": "8x H100 SXM5 (europe-central-1)",
        "gpu_type": "H100",
        "gpu_count": 8,
        "vram_per_gpu": 80,
        "price_per_hour_eur": 26.32,
        "note": "fallback — API nedostupné",
    },
]


def classify_gpu(instance_type_name: str, gpu_name: str) -> tuple[str, int, int] | None:
    """Vráti (gpu_type, gpu_count, vram_per_gpu) alebo None."""
    name_lower = (instance_type_name + " " + gpu_name).lower()
    if "h200" in name_lower:
        gpu_type = "H200"
        vram = 141
    elif "h100" in name_lower:
        gpu_type = "H100"
        vram = 80
    else:
        return None

    # GPU count z instance_type_name, napr. "gpu_1x_h100_sxm5"
    import re
    m = re.search(r"(\d+)x", instance_type_name.lower())
    count = int(m.group(1)) if m else 1
    return gpu_type, count, vram


def main() -> None:
    eprint(f"[Lambda] Volám API: {API_URL}")

    with get_client() as client:
        try:
            r = client.get(API_URL, timeout=20)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            eprint(f"[Lambda] API zlyhalo: {exc} — použijem fallback")
            emit({
                "provider_id": "lambda",
                "type": "gpu",
                "source_url": USER_FACING_URL,
                "pricing_api_url": API_URL,
                "fetched_at": now_iso(),
                "instances": FALLBACK,
                "warning": "API nedostupné — použité fallback hodnoty",
            })
            return

    instance_types = data.get("data", {})
    instances_out = []

    for type_name, info in instance_types.items():
        specs = info.get("instance_type", {})
        gpu_desc = specs.get("description", "")
        gpu_model = (specs.get("gpu_type") or {}).get("name", "")

        classified = classify_gpu(type_name, gpu_model or gpu_desc)
        if classified is None:
            continue

        gpu_type, gpu_count, vram = classified

        # Cena
        price_cents_usd = specs.get("price_cents_per_hour", 0)
        if price_cents_usd <= 0:
            continue
        price_usd = price_cents_usd / 100.0
        price_eur = usd_to_eur(price_usd)

        # Skontrolujeme dostupné regióny
        regions = info.get("regions_with_capacity_available", [])
        eu_available = any(
            r.get("name", "") in EU_REGIONS for r in regions
        )
        all_regions = [r.get("name", "") for r in regions]
        eu_region_note = "europe-central-1" if eu_available else "EU nedostupné"

        eprint(
            f"[Lambda] {type_name}: {gpu_count}x {gpu_type} "
            f"${price_usd:.2f}/hod → {price_eur:.2f} EUR/hod | "
            f"EU: {eu_region_note}"
        )

        instances_out.append({
            "id": f"lam-{type_name}",
            "name": f"{type_name.replace('_', ' ')} ({eu_region_note})",
            "gpu_type": gpu_type,
            "gpu_count": gpu_count,
            "vram_per_gpu": vram,
            "price_per_hour_usd": price_usd,
            "price_per_hour_eur": price_eur,
            "eu_available": eu_available,
            "currency_note": "converted from USD via ECB API",
        })

    if not instances_out:
        eprint("[Lambda] API dostupné ale žiadne H100/H200 inštancie — použijem fallback")
        instances_out = FALLBACK

    emit({
        "provider_id": "lambda",
        "type": "gpu",
        "source_url": USER_FACING_URL,
        "pricing_api_url": API_URL,
        "fetched_at": now_iso(),
        "instances": instances_out,
    })


if __name__ == "__main__":
    main()
