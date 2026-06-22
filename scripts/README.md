# Pricing Parser Scripts

Sada Python skriptov na automatické parsovanie cien GPU cloudu, API tokenov a hardware od overených EU zdrojov.

## Pravidlá

- **Len EU** poskytovatelia a regióny
- **Žiadne halucinácie** — každá hodnota musí byť stiahnutá zo zdrojovej URL
- Ak parser zlyhá, `update_constants.py` zachová pôvodnú hodnotu a vypíše varovanie
- EUR/USD konverzia cez ECB API (aktuálny kurz)

## Inštalácia

```bash
cd scripts
pip install -r requirements.txt
```

## Spustenie

### Aktualizácia všetkých zdrojov (dry-run — len zobrazí zmeny):
```bash
python update_constants.py --dry-run
```

### Skutočný update `constants.ts`:
```bash
python update_constants.py
```

### Testovanie jednotlivého parsera:
```bash
python sources/parse_aws_gpu.py
python sources/parse_azure_gpu.py
python sources/parse_ovhcloud_gpu.py
python sources/parse_nebius_gpu.py
python sources/parse_lambda_gpu.py
python sources/parse_nebius_api.py
python sources/parse_scaleway_api.py
python sources/parse_tensorx_api.py
python sources/parse_aws_bedrock_api.py
python sources/parse_greenpt_api.py
python sources/parse_inceptron_api.py
python sources/parse_smicro.py
```

## Štruktúra výstupu parserov

Každý parser vypisuje na stdout JSON v tomto formáte:

```json
{
  "source_url": "https://...",
  "fetched_at": "2026-06-22T21:00:00Z",
  "provider_id": "aws",
  "type": "gpu",
  "instances": [
    {
      "id": "aws-p5",
      "name": "p5.48xlarge (8x H100)",
      "gpu_type": "H100",
      "gpu_count": 8,
      "vram_per_gpu": 80,
      "price_per_hour_eur": 55.04,
      "currency_note": "converted from USD at ECB rate"
    }
  ]
}
```

Pre API poskytovatelia:
```json
{
  "source_url": "https://...",
  "fetched_at": "2026-06-22T21:00:00Z",
  "provider_id": "nebius-api",
  "type": "api",
  "models": [
    {
      "model_id": "deepseek-v4",
      "model_name": "DeepSeek Pro v4",
      "input_price_per_million_eur": 1.75,
      "output_price_per_million_eur": 3.50,
      "is_available": true
    }
  ]
}
```

## Manuálne udržiavané dáta

- `sources/benchmarks_manual.json` — TPS hodnoty pre jednotlivé GPU typy
- `sources/verda_manual.json` — Verda GPU ceny (nemajú verejný cenník)

Tieto súbory skript **nikdy neprepíše** — sú pod správou git.
Skript vypíše varovanie, ak sú dáta staršie ako 30 dní.
