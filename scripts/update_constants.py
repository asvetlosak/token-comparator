"""
update_constants.py — Hlavný skript na aktualizáciu src/data/constants.ts

Spustenie:
  python update_constants.py            # Aktualizuje constants.ts
  python update_constants.py --dry-run  # Len zobrazí zmeny, nezapíše

Postup:
1. Spustí každý parser (sources/parse_*.py)
2. Validuje dáta (EU región, cena > 0, známy GPU typ)
3. Ak parser zlyhá → zachová pôvodnú hodnotu, vypíše varovanie
4. ECB API pre konverziu USD → EUR
5. Prepíše bloky GPU_PROVIDERS, API_PROVIDERS v constants.ts
6. Pridá komentár so zdrojom a dátumom nad každú hodnotu
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Cesty
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
SOURCES_DIR = SCRIPT_DIR / "sources"
REPO_ROOT = SCRIPT_DIR.parent
CONSTANTS_TS = REPO_ROOT / "src" / "data" / "constants.ts"

# ---------------------------------------------------------------------------
# Parsery: (script_path, provider_id, type)
# ---------------------------------------------------------------------------

PARSERS: list[tuple[Path, str, str]] = [
    # GPU Cloud
    (SOURCES_DIR / "parse_aws_gpu.py",         "aws",            "gpu"),
    (SOURCES_DIR / "parse_azure_gpu.py",        "azure",          "gpu"),
    (SOURCES_DIR / "parse_nebius_gpu.py",        "nebius",         "gpu"),
    (SOURCES_DIR / "parse_ovhcloud_gpu.py",      "ovhcloud",       "gpu"),
    (SOURCES_DIR / "parse_scaleway_gpu.py",      "scaleway-gpu",   "gpu"),
    # API Providers
    (SOURCES_DIR / "parse_nebius_api.py",        "nebius-api",     "api"),
    (SOURCES_DIR / "parse_scaleway_api.py",      "scaleway",       "api"),
    (SOURCES_DIR / "parse_tensorx_api.py",       "tensorx",        "api"),
    (SOURCES_DIR / "parse_aws_bedrock_api.py",   "aws-bedrock-api","api"),
    (SOURCES_DIR / "parse_greenpt_api.py",       "greenpt-api",    "api"),
    (SOURCES_DIR / "parse_inceptron_api.py",     "inceptron-api",  "api"),
    # Hardware
    (SOURCES_DIR / "parse_smicro.py",            "on-premise",     "hardware"),
]

# Manuálne udržiavané dáta (nikdy neprepisujeme)
VERDA_MANUAL = SOURCES_DIR / "verda_manual.json"
BENCHMARKS_MANUAL = SOURCES_DIR / "benchmarks_manual.json"

STALE_DAYS = 30  # Varovanie ak sú manuálne dáta staršie ako X dní

# ---------------------------------------------------------------------------
# Hlavná logika
# ---------------------------------------------------------------------------


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def run_parser(script: Path) -> dict[str, Any] | None:
    """Spustí parser subprocess a vráti JSON výstup alebo None pri chybe."""
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            log(f"  ⚠️  Parser {script.name} skončil s chybou (kód {result.returncode})")
            if result.stderr:
                log(f"     STDERR: {result.stderr.strip()[:300]}")
            return None

        # Stderr = logovanie parsera (info pre nás)
        if result.stderr:
            for line in result.stderr.strip().splitlines():
                log(f"     {line}")

        if not result.stdout.strip():
            log(f"  ⚠️  Parser {script.name} vypísal prázdny výstup")
            return None

        return json.loads(result.stdout)

    except subprocess.TimeoutExpired:
        log(f"  ⚠️  Parser {script.name} — timeout (>120s)")
        return None
    except json.JSONDecodeError as e:
        log(f"  ⚠️  Parser {script.name} — neplatný JSON: {e}")
        return None
    except Exception as e:
        log(f"  ⚠️  Parser {script.name} — chyba: {e}")
        return None


def check_staleness(json_path: Path) -> None:
    """Upozorní ak sú manuálne dáta staršie ako STALE_DAYS dní."""
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        last_verified = data.get("last_verified", "")
        if not last_verified:
            return
        verified_date = datetime.fromisoformat(last_verified).date()
        today = datetime.now(timezone.utc).date()
        delta = (today - verified_date).days
        if delta > STALE_DAYS:
            log(
                f"  ⚠️  VAROVANIE: {json_path.name} je stary {delta} dní "
                f"(overené {last_verified}) — zvažte manuálnu aktualizáciu!"
            )
    except Exception:
        pass


def load_manual_data() -> tuple[dict, dict]:
    """Načíta Verda a benchmarks manuálne JSON."""
    verda = {}
    benchmarks = {}

    if VERDA_MANUAL.exists():
        check_staleness(VERDA_MANUAL)
        try:
            verda = json.loads(VERDA_MANUAL.read_text(encoding="utf-8"))
        except Exception as e:
            log(f"  ⚠️  Chyba pri čítaní {VERDA_MANUAL.name}: {e}")

    if BENCHMARKS_MANUAL.exists():
        check_staleness(BENCHMARKS_MANUAL)
        try:
            benchmarks = json.loads(BENCHMARKS_MANUAL.read_text(encoding="utf-8"))
        except Exception as e:
            log(f"  ⚠️  Chyba pri čítaní {BENCHMARKS_MANUAL.name}: {e}")

    return verda, benchmarks


# ---------------------------------------------------------------------------
# TypeScript generátor
# ---------------------------------------------------------------------------

def eur_per_month(eur_per_hour: float) -> float:
    return round(eur_per_hour * 730, 2)


def generate_gpu_providers(
    parsed_data: dict[str, dict],
    verda_data: dict,
    benchmarks: dict,
    existing_ts: str,
) -> str:
    """Generuje blok GPU_PROVIDERS pre constants.ts."""

    # Poradie providerov (zachováme pôvodné, bez verda a lambda)
    PROVIDER_ORDER = [
        "aws", "azure", "nebius", "ovhcloud", "scaleway-gpu", "on-premise"
    ]

    # Metadata providerov (nezávislé od cien)
    PROVIDER_META = {
        "aws": {
            "name": "AWS",
            "region": "EU (Frankfurt eu-central-1, Ireland eu-west-1)",
            "flag": "🇪🇺",
        },
        "azure": {
            "name": "Azure",
            "region": "EU (West Europe)",
            "flag": "🇪🇺",
        },
        "verda": {
            "name": "Verda",
            "region": "EU (Finland)",
            "flag": "🇫🇮",
        },
        "lambda": {
            "name": "Lambda",
            "region": "EU (Germany europe-central-1)",
            "flag": "🇩🇪",
        },
        "nebius": {
            "name": "Nebius",
            "region": "EU (Finland eu-north1)",
            "flag": "🇫🇮",
        },
        "ovhcloud": {
            "name": "OVHcloud",
            "region": "EU (France/Germany)",
            "flag": "🇫🇷",
        },
        "scaleway-gpu": {
            "name": "Scaleway",
            "region": "EU (France fr-par-2)",
            "flag": "🇫🇷",
        },
        "on-premise": {
            "name": "Vlastná serverovňa (Nákup)",
            "region": "Local",
            "flag": "🏢",
        },
    }

    lines: list[str] = []
    lines.append("")
    lines.append("export const GPU_PROVIDERS: GPUProvider[] = [")

    for provider_id in PROVIDER_ORDER:
        meta = PROVIDER_META.get(provider_id, {})
        data = parsed_data.get(provider_id)

        # Špeciálny prípad: Verda (manuálne dáta)
        if provider_id == "verda":
            source_url = verda_data.get("source_url", "https://verda.com")
            contact_note = verda_data.get("contact_note", "")
            fetched_at = verda_data.get("last_verified", "manual")
            instances = verda_data.get("instances", [])
            lines.append(f"  {{")
            lines.append(f"    id: 'verda',")
            lines.append(f"    name: '{meta.get('name', 'Verda')}',")
            lines.append(f"    region: '{meta.get('region', 'EU (Finland)')}',")
            lines.append(f"    flag: '{meta.get('flag', '🇫🇮')}',")
            lines.append(f"    // source: {source_url}")
            lines.append(f"    // note: {contact_note}")
            lines.append(f"    // last_verified: {fetched_at}")
            lines.append(f"    pricingUrl: '{source_url}',")
            lines.append(f"    instances: [")
            for inst in instances:
                lines.append(f"      // {inst['name']} — {inst['price_per_hour_eur']} EUR/hod")
                lines.append(
                    f"      {{ id: '{inst['id']}', name: '{inst['name']}', "
                    f"gpuType: '{inst['gpu_type']}', gpuCount: {inst['gpu_count']}, "
                    f"vramPerGPU: {inst['vram_per_gpu']}, "
                    f"pricePerHour: {inst['price_per_hour_eur']}, "
                    f"pricePerMonth: {eur_per_month(inst['price_per_hour_eur'])} }},"
                )
            lines.append(f"    ],")
            lines.append(f"  }},")
            continue

        # Hardware provideri (on-premise)
        if provider_id == "on-premise":
            source_url = (data or {}).get("source_url", "https://smicro.sk")
            fetched_at = (data or {}).get("fetched_at", "unknown")
            instances = (data or {}).get("instances", [])
            lines.append(f"  {{")
            lines.append(f"    id: 'on-premise',")
            lines.append(f"    name: '{meta.get('name', 'Vlastná serverovňa')}',")
            lines.append(f"    region: '{meta.get('region', 'Local')}',")
            lines.append(f"    flag: '{meta.get('flag', '🏢')}',")
            lines.append(f"    // source: {source_url}")
            lines.append(f"    // fetched_at: {fetched_at}")
            lines.append(f"    pricingUrl: '{source_url}',")
            lines.append(f"    instances: [")
            for inst in instances:
                cost = inst.get("hardware_cost_eur", 0)
                lines.append(
                    f"      // {inst['name']} — {cost:,.0f} EUR nákupná cena"
                )
                lines.append(
                    f"      {{ id: '{inst['id']}', name: '{inst['name']}', "
                    f"gpuType: '{inst['gpu_type']}', gpuCount: {inst['gpu_count']}, "
                    f"vramPerGPU: {inst['vram_per_gpu']}, "
                    f"pricePerHour: 0, pricePerMonth: 0, "
                    f"hardwareCostPerNode: {int(cost)}"
                )
                
                # Voliteľné výkonové parametre
                opt_fields = []
                if "tflops_fp8" in inst:
                    opt_fields.append(f"tflopsFP8: {inst['tflops_fp8']}")
                if "tflops_fp16" in inst:
                    opt_fields.append(f"tflopsFP16: {inst['tflops_fp16']}")
                if "memory_bandwidth_gbs" in inst:
                    opt_fields.append(f"memoryBandwidthGBs: {inst['memory_bandwidth_gbs']}")
                if "item_url" in inst and inst["item_url"]:
                    opt_fields.append(f"itemUrl: '{inst['item_url']}'")
                
                if opt_fields:
                    lines[-1] += ", " + ", ".join(opt_fields)
                lines[-1] += " },"

            lines.append(f"    ],")
            lines.append(f"  }},")
            continue

        # Bežní GPU cloud provideri
        if data is None:
            log(f"  ⚠️  Žiadne dáta pre {provider_id} — zachovávam pôvodný blok")
            # Extrahuj pôvodný blok z existing_ts (jednoduché náhradné riešenie)
            original_block = _extract_provider_block(existing_ts, provider_id)
            if original_block:
                lines.extend(f"  {line}" for line in original_block.splitlines())
            continue

        source_url = data.get("source_url", "")
        pricing_api = data.get("pricing_api_url") or data.get("pricing_api_urls", [""])[0] if isinstance(data.get("pricing_api_urls"), list) else data.get("pricing_api_url", "")
        fetched_at = data.get("fetched_at", "unknown")
        instances = data.get("instances", [])

        # Zoskupíme inštancie pre rovnakého providera (pre AWS: berieme najlacnejšiu cenu z EU regiónov)
        best_instances = _deduplicate_instances(instances, provider_id)

        lines.append(f"  {{")
        lines.append(f"    id: '{provider_id}',")
        lines.append(f"    name: '{meta.get('name', provider_id)}',")
        lines.append(f"    region: '{meta.get('region', 'EU')}',")
        lines.append(f"    flag: '{meta.get('flag', '🇪🇺')}',")
        lines.append(f"    // source: {source_url}")
        if pricing_api:
            lines.append(f"    // pricing_api: {pricing_api}")
        lines.append(f"    // fetched_at: {fetched_at}")
        lines.append(f"    pricingUrl: '{source_url}',")
        lines.append(f"    instances: [")

        for inst in best_instances:
            price_eur = inst.get("price_per_hour_eur", 0)
            lines.append(
                f"      // {inst.get('name', inst.get('id'))} — "
                f"{price_eur:.4f} EUR/hod"
            )
            lines.append(
                f"      {{ id: '{inst['id']}', name: '{inst['name']}', "
                f"gpuType: '{inst['gpu_type']}', gpuCount: {inst['gpu_count']}, "
                f"vramPerGPU: {inst['vram_per_gpu']}, "
                f"pricePerHour: {price_eur}, "
                f"pricePerMonth: {eur_per_month(price_eur)}"
            )
            
            # Voliteľné výkonové parametre
            opt_fields = []
            if "tflops_fp8" in inst:
                opt_fields.append(f"tflopsFP8: {inst['tflops_fp8']}")
            if "tflops_fp16" in inst:
                opt_fields.append(f"tflopsFP16: {inst['tflops_fp16']}")
            if "memory_bandwidth_gbs" in inst:
                opt_fields.append(f"memoryBandwidthGBs: {inst['memory_bandwidth_gbs']}")
            if "hardware_cost_eur" in inst:
                opt_fields.append(f"hardwareCostPerNode: {int(inst['hardware_cost_eur'])}")
            if "item_url" in inst and inst["item_url"]:
                opt_fields.append(f"itemUrl: '{inst['item_url']}'")
            
            if opt_fields:
                lines[-1] += ", " + ", ".join(opt_fields)
            lines[-1] += " },"


        lines.append(f"    ],")
        lines.append(f"  }},")

    lines.append("];")
    return "\n".join(lines)


def _deduplicate_instances(instances: list[dict], provider_id: str) -> list[dict]:
    """Pre AWS (viac regiónov) zachováme len unikátne ID s najnižšou cenou."""
    seen: dict[str, dict] = {}
    for inst in instances:
        base_id = re.sub(r"-eu-\w+", "", inst.get("id", ""))  # strip region suffix
        base_id = re.sub(r"-\w+europe\w*", "", base_id)
        if base_id not in seen:
            seen[base_id] = {**inst, "id": base_id}
        else:
            # Zachovaj lacnejšiu cenu
            if inst.get("price_per_hour_eur", 999) < seen[base_id].get("price_per_hour_eur", 999):
                seen[base_id] = {**inst, "id": base_id}
    return list(seen.values())


def _extract_provider_block(ts_content: str, provider_id: str) -> str:
    """Extrahuje pôvodný blok providera z TS súboru (záložné riešenie)."""
    pattern = rf"id:\s*['\"]({re.escape(provider_id)})['\"]"
    match = re.search(pattern, ts_content)
    if not match:
        return ""
    # Nájdeme ohraničenie objektu
    start = ts_content.rfind("{", 0, match.start())
    depth = 0
    for i, ch in enumerate(ts_content[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return ts_content[start : i + 1] + ","
    return ""


def generate_api_providers(parsed_data: dict[str, dict], existing_ts: str) -> str:
    """Generuje blok API_PROVIDERS pre constants.ts."""

    PROVIDER_ORDER = [
        "nebius-api", "scaleway", "greenpt-api", "tensorx",
        "aws-bedrock-api", "inceptron-api", "infercom-api",
    ]

    PROVIDER_META = {
        "nebius-api": {
            "name": "Nebius Token Factory",
            "region": "EU (Finland eu-north1)",
            "flag": "🇫🇮",
        },
        "scaleway": {
            "name": "Scaleway",
            "region": "EU (France/Netherlands)",
            "flag": "🇪🇺",
        },
        "greenpt-api": {
            "name": "GreenPT",
            "region": "EU (Netherlands)",
            "flag": "🇳🇱",
        },
        "tensorx": {
            "name": "TensorX",
            "region": "EU (Sweden)",
            "flag": "🇸🇪",
        },
        "aws-bedrock-api": {
            "name": "AWS Bedrock",
            "region": "EU (Frankfurt eu-central-1, Paris eu-west-3)",
            "flag": "🇪🇺",
        },
        "inceptron-api": {
            "name": "Inceptron",
            "region": "EU (Sweden)",
            "flag": "🇸🇪",
        },
        "infercom-api": {
            "name": "Infercom",
            "region": "EU (Luxembourg)",
            "flag": "🇱🇺",
        },
    }

    lines: list[str] = []
    lines.append("")
    lines.append("export const API_PROVIDERS: APIProvider[] = [")

    MODEL_ORDER = ["deepseek-v4", "glm-5.2", "minimax-m3", "qwen-3.6"]

    for provider_id in PROVIDER_ORDER:
        meta = PROVIDER_META.get(provider_id, {})
        data = parsed_data.get(provider_id)

        # Infercom nemá parser (žiadna verejná API/cenník) — zachovávame pôvodnú hodnotu
        if provider_id == "infercom-api":
            original = _extract_provider_block(existing_ts, provider_id)
            if original:
                lines.append(f"  // source: https://infercom.ai/pricing/ (manuálne — žiadne verejné API)")
                for line in original.splitlines():
                    lines.append(f"  {line}")
            continue

        if data is None:
            log(f"  ⚠️  Žiadne dáta pre {provider_id} — zachovávam pôvodný blok")
            original = _extract_provider_block(existing_ts, provider_id)
            if original:
                for line in original.splitlines():
                    lines.append(f"  {line}")
            continue

        source_url = data.get("source_url", "")
        fetched_at = data.get("fetched_at", "unknown")
        models = data.get("models", [])

        # Index modelov podľa model_id
        model_index = {m["model_id"]: m for m in models}

        lines.append(f"  {{")
        lines.append(f"    id: '{provider_id}',")
        lines.append(f"    name: '{meta.get('name', provider_id)}',")
        lines.append(f"    region: '{meta.get('region', 'EU')}',")
        lines.append(f"    flag: '{meta.get('flag', '🇪🇺')}',")
        lines.append(f"    // source: {source_url}")
        lines.append(f"    // fetched_at: {fetched_at}")
        lines.append(f"    pricingUrl: '{source_url}',")
        lines.append(f"    models: [")

        for model_id in MODEL_ORDER:
            m = model_index.get(model_id, {
                "model_id": model_id,
                "model_name": model_id,
                "input_price_per_million_eur": 0,
                "output_price_per_million_eur": 0,
                "is_available": False,
            })
            inp = m.get("input_price_per_million_eur", 0)
            out = m.get("output_price_per_million_eur", 0)
            avail = "true" if m.get("is_available") else "false"
            note = m.get("note", "")
            lines.append(
                f"      // {model_id} — in: {inp}/M, out: {out}/M | {note}"
            )
            lines.append(
                f"      {{ modelId: '{model_id}', modelName: '{m.get('model_name', model_id)}', "
                f"inputPricePerMillion: {inp}, outputPricePerMillion: {out}, "
                f"isAvailable: {avail} }},"
            )

        lines.append(f"    ],")
        lines.append(f"  }},")

    lines.append("];")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Patch constants.ts
# ---------------------------------------------------------------------------

GPU_PROVIDERS_RE = re.compile(
    r"(export const GPU_PROVIDERS: GPUProvider\[\] = \[)(.*?)(\];)",
    re.DOTALL,
)
API_PROVIDERS_RE = re.compile(
    r"(export const API_PROVIDERS: APIProvider\[\] = \[)(.*?)(\];)",
    re.DOTALL,
)


def patch_constants_ts(
    gpu_block: str,
    api_block: str,
    original: str,
    dry_run: bool,
) -> None:
    """Nahradí GPU_PROVIDERS a API_PROVIDERS bloky v constants.ts."""

    # Extrahujeme len obsah (bez export const ... = [...];)
    def inner(block: str) -> str:
        # Strip prvý riadok (export const ...) a posledný (];)
        lines = block.strip().splitlines()
        if lines and lines[0].startswith("export const"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "];":
            lines = lines[:-1]
        return "\n".join(lines)

    new_content = original

    # Patch GPU_PROVIDERS
    m = GPU_PROVIDERS_RE.search(new_content)
    if m:
        new_gpu = f"export const GPU_PROVIDERS: GPUProvider[] = [{inner(gpu_block)}\n];"
        new_content = new_content[: m.start()] + new_gpu + new_content[m.end() :]
    else:
        log("  ⚠️  GPU_PROVIDERS blok nebol nájdený v constants.ts")

    # Patch API_PROVIDERS
    m = API_PROVIDERS_RE.search(new_content)
    if m:
        new_api = f"export const API_PROVIDERS: APIProvider[] = [{inner(api_block)}\n];"
        new_content = new_content[: m.start()] + new_api + new_content[m.end() :]
    else:
        log("  ⚠️  API_PROVIDERS blok nebol nájdený v constants.ts")

    # Pridaj hlavičkový komentár s dátumom
    ts_header_re = re.compile(r"^// ={20,}\n// constants\.ts.*?\n// ={20,}", re.MULTILINE)
    new_header = (
        f"// {'=' * 76}\n"
        f"// constants.ts — Všetky dátové sady, modely, GPU a API providery\n"
        f"// Posledná aktualizácia: {now_iso()} (update_constants.py)\n"
        f"// {'=' * 76}\n"
        f"// Obsahuje len EU poskytovateľov s reálnymi odkazmi na cenníky.\n"
        f"// {'=' * 76}"
    )
    new_content = ts_header_re.sub(new_header, new_content)

    if dry_run:
        log("\n" + "=" * 60)
        log("DRY RUN — constants.ts by bol prepísaný takto:")
        log("=" * 60)
        preview = new_content[:3000] + "\n...[skrátené]" if len(new_content) > 3000 else new_content
        # Použijem UTF-8 výstup explicitne (obídeme cp1252 na Windows)
        sys.stdout.buffer.write(preview.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
        sys.stdout.buffer.flush()
        log("\n[DRY RUN] Žiadne zmeny neboli zapísané.")

    else:
        # Záloha
        backup_path = CONSTANTS_TS.with_suffix(".ts.bak")
        backup_path.write_text(original, encoding="utf-8")
        log(f"  📋 Záloha uložená: {backup_path}")

        CONSTANTS_TS.write_text(new_content, encoding="utf-8")
        log(f"  ✅ constants.ts aktualizovaný!")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aktualizuje ceny v constants.ts z overených zdrojov"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Zobrazí zmeny bez zápisu do súboru",
    )
    args = parser.parse_args()

    log(f"\n{'=' * 60}")
    log(f"  Token Comparator — Update Constants")
    log(f"  {now_iso()}")
    log(f"{'=' * 60}\n")

    if not CONSTANTS_TS.exists():
        log(f"  ❌ Súbor nenájdený: {CONSTANTS_TS}")
        sys.exit(1)

    original_ts = CONSTANTS_TS.read_text(encoding="utf-8")

    # Načítaj manuálne dáta
    log("📂 Načítavam manuálne dáta...")
    verda_data, benchmarks = load_manual_data()

    # Spustí všetky parsery
    parsed: dict[str, dict] = {}
    for script, provider_id, ptype in PARSERS:
        log(f"\n🔍 Spúšťam parser: {script.name} [{provider_id}]")
        result = run_parser(script)
        if result:
            if result.get("warning"):
                log(f"  ⚠️  {result['warning']}")
            parsed[provider_id] = result
            instance_count = len(result.get("instances", result.get("models", [])))
            log(f"  ✅ OK — {instance_count} záznamov")
        else:
            log(f"  ❌ Parser zlyhal — zachovám pôvodnú hodnotu z constants.ts")

    # Generuj nové bloky
    log("\n✍️  Generujem nové bloky...")
    gpu_block = generate_gpu_providers(parsed, verda_data, benchmarks, original_ts)
    api_block = generate_api_providers(parsed, original_ts)

    # Zapiš (alebo dry-run)
    patch_constants_ts(gpu_block, api_block, original_ts, args.dry_run)

    log("\n✅ Hotovo!\n")


if __name__ == "__main__":
    main()
