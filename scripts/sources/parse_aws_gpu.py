"""
parse_aws_gpu.py — AWS EC2 GPU ceny pre EU regióny

Zdroj (machine-readable JSON):
  Frankfurt: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/eu-central-1/index.json
  Ireland:   https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/eu-west-1/index.json

Cieľová URL pre používateľa (pricelist s filtrom):
  https://aws.amazon.com/ec2/pricing/on-demand/?nc2=type_a&nc1=h_ls#eu-central-1

POZNÁMKA: Parser získava len reálne dostupné GPU inštancie z EU regiónov (p4d, p4de, g6e).
Fallback z US pre H100 (p5) je odstránený, aby dáta zodpovedali striktnej požiadavke "len EU infra".
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sources.shared import get_client, usd_to_eur, now_iso, emit, eprint, die

# ---------------------------------------------------------------------------
# Konfigurácia
# ---------------------------------------------------------------------------

# Priame linky na cenníky pre konkrétne rodiny inštancií
PRICING_URLS = {
    "eu-central-1": (
        "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2"
        "/current/eu-central-1/index.json"
    ),
    "eu-west-1": (
        "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2"
        "/current/eu-west-1/index.json"
    ),
}

# Odkaz pre používateľa — filtrovaný cenník pre EU regióny a p5/p5e family
USER_FACING_URL = (
    "https://aws.amazon.com/ec2/pricing/on-demand/?nc2=type_a&nc1=h_ls"
    "#eu-central-1"
)

TARGET_FAMILIES = {"p4d", "p4de", "g6e"}

KNOWN_INSTANCES: dict[str, dict] = {
    "p4de.24xlarge": {
        "id": "aws-p4de",
        "name": "p4de.24xlarge (8x A100 80GB)",
        "gpu_type": "A100",
        "gpu_count": 8,
        "vram_per_gpu": 80,
        "tflops_fp16": 2496,  # 8 * 312 TFLOPS (A100 Tensor Core FP16)
        "memory_bandwidth_gbs": 16232,  # 8 * 2039 GB/s
    },
    "p4d.24xlarge": {
        "id": "aws-p4d",
        "name": "p4d.24xlarge (8x A100 40GB)",
        "gpu_type": "A100",
        "gpu_count": 8,
        "vram_per_gpu": 40,
        "tflops_fp16": 2496,  # 8 * 312 TFLOPS
        "memory_bandwidth_gbs": 12440,  # 8 * 1555 GB/s
    },
    "g6e.48xlarge": {
        "id": "aws-g6e",
        "name": "g6e.48xlarge (8x L40S)",
        "gpu_type": "L40S",
        "gpu_count": 8,
        "vram_per_gpu": 48,
        "tflops_fp8": 5856,  # 8 * 733 TFLOPS FP8
        "memory_bandwidth_gbs": 6912,  # 8 * 864 GB/s
    },
}


def parse_region(client, region: str, url: str) -> dict[str, float]:
    """Vráti {instanceType: price_per_hour_usd} pre daný región."""
    eprint(f"[AWS] Sťahujem cenník pre {region} ({url}) ...")
    try:
        r = client.get(url, timeout=60)
        r.raise_for_status()
    except Exception as exc:
        die(f"AWS {region}: stiahnutie zlyhalo — {exc}")

    data = r.json()
    products = data.get("products", {})
    terms = data.get("terms", {}).get("OnDemand", {})

    prices: dict[str, float] = {}
    for sku, product in products.items():
        attrs = product.get("attributes", {})
        instance_type = attrs.get("instanceType", "")
        family = instance_type.split(".")[0] if "." in instance_type else ""
        if family not in TARGET_FAMILIES:
            continue
        if attrs.get("operatingSystem") != "Linux":
            continue
        if attrs.get("tenancy") != "Shared":
            continue
        if attrs.get("preInstalledSw") != "NA":
            continue
        if attrs.get("capacitystatus") != "Used":
            continue

        # Cena: terms.OnDemand.{sku}.{offerTermCode}.priceDimensions.{rateCode}.pricePerUnit.USD
        sku_terms = terms.get(sku, {})
        for term in sku_terms.values():
            for dim in term.get("priceDimensions", {}).values():
                usd_str = dim.get("pricePerUnit", {}).get("USD", "")
                if usd_str and float(usd_str) > 0:
                    prices[instance_type] = float(usd_str)

    return prices


def main() -> None:
    instances_out = []

    with get_client() as client:
        for region, url in PRICING_URLS.items():
            prices = parse_region(client, region, url)
            for instance_type, meta in KNOWN_INSTANCES.items():
                if instance_type in prices:
                    price_usd = prices[instance_type]
                    price_eur = usd_to_eur(price_usd)
                    eprint(
                        f"[AWS] {instance_type} @ {region}: "
                        f"${price_usd:.2f}/hod → {price_eur:.2f} EUR/hod"
                    )
                    instances_out.append(
                        {
                            **meta,
                            "region": region,
                            "price_per_hour_usd": price_usd,
                            "price_per_hour_eur": price_eur,
                            "currency_note": "converted from USD via ECB API",
                        }
                    )
                else:
                    pass

    if not instances_out:
        eprint("[AWS] ⚠️ Nenašli sa žiadne inštancie v EU!")

    emit({
        "provider_id": "aws",
        "type": "cloud",
        "source_url": USER_FACING_URL,
        "fetched_at": now_iso(),
        "instances": instances_out
    })

if __name__ == "__main__":
    main()
