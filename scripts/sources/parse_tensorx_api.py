"""
parse_tensorx_api.py — TensorX LLM API ceny

Zdroj (HTML cenník):
  https://tensorx.ai/pricing/

TensorX je EU-sovereign provider (Švédsko), ponúka OpenAI-kompatibilné API.
Parsujeme ceny za milión tokenov pre cieľové modely.
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

# TensorX blokuje jednoduché scrapery na /pricing/ (403)
# Skúšame viacero URL
SOURCE_URLS = [
    "https://tensorx.ai/pricing/",
    "https://tensorx.ai/models",
    "https://tensorx.ai/",
]
SOURCE_URL = SOURCE_URLS[0]  # primárna URL pre metadata

TARGET_MODELS = [
    {
        "model_id": "deepseek-v4",
        "model_name": "DeepSeek Pro v4",
        # TensorX model identifikátory
        "search_keywords": ["deepseek-v4-pro", "deepseek/deepseek-v4"],
    },
    {
        "model_id": "glm-5.2",
        "model_name": "GLM 5.2",
        "search_keywords": ["glm-5.2", "z-ai/glm-5.2", "glm 5.2"],
    },
    {
        "model_id": "minimax-m3",
        "model_name": "MiniMax M3",
        "search_keywords": ["minimax-m3", "minimax/minimax-m3"],
    },
    {
        "model_id": "qwen-3.6",
        "model_name": "Qwen 3.6",
        "search_keywords": ["qwen3", "qwen-3", "qwen 3"],
    },
]

# Záložné hodnoty z posledného overeného cenníka TensorX
# Zdroj: https://tensorx.ai/pricing/ (overené 2026-06-22)
FALLBACK_PRICES = {
    "deepseek-v4": (1.75, 3.50),   # deepseek/deepseek-v4-pro
    "glm-5.2": (1.50, 4.50),       # z-ai/glm-5.2
    "minimax-m3": (0.40, 2.00),    # minimax/minimax-m3
    "qwen-3.6": (0.06, 0.25),      # Qwen 3.6 (35B) - ak je dostupný
}

# Regulárne výrazy pre ceny
PRICE_USD_RE = re.compile(r"\$\s*([\d]+\.[\d]+)")
PRICE_NUM_RE = re.compile(r"([\d]+\.[\d]+)")


def find_price_in_row(text: str) -> tuple[float, float] | None:
    """Nájde (input_price, output_price) v texte riadku."""
    prices = PRICE_USD_RE.findall(text)
    if len(prices) >= 2:
        return float(prices[0]), float(prices[1])
    # Skúsime bez $ symbolu ak sú dve čísla
    nums = PRICE_NUM_RE.findall(text)
    nums = [float(n) for n in nums if 0.001 < float(n) < 100]
    if len(nums) >= 2:
        return nums[0], nums[1]
    return None


def main() -> None:
    eprint(f"[TensorX] Pokúšam sa o stiahnutie z viacerých URL (cez Playwright)...")

    html_content = None
    used_url = None

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Spustíme headless chromium
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )

            for url in SOURCE_URLS:
                try:
                    eprint(f"[TensorX] Navštevujem {url} ...")
                    page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    
                    # Počkáme 5 sekúnd, aby sa JS vyrenderoval a Cloudflare challenge prešiel
                    page.wait_for_timeout(5000)
                    
                    html = page.content()
                    
                    # Zjednodušená detekcia či sme prešli: Hľadáme naše modely v texte
                    text_lower = html.lower()
                    if "deepseek" in text_lower or "glm" in text_lower or "minimax" in text_lower or "qwen" in text_lower:
                        html_content = html
                        used_url = url
                        eprint(f"[TensorX] OK: {url} (našli sa modely)")
                        break
                    else:
                        eprint(f"[TensorX] {url} -> modely nenájdené, skúšam ďalšiu...")
                except Exception as exc:
                    eprint(f"[TensorX] {url} -> chyba: {exc}")

            browser.close()
    except ImportError:
        eprint("[TensorX] Playwright nie je nainštalovaný. Spustite 'pip install playwright' a 'playwright install chromium'")
    except Exception as exc:
        eprint(f"[TensorX] Chyba pri inicializácii Playwright: {exc}")

    if html_content is None:
        eprint("[TensorX] Všetky URL zlyhalé alebo blokované — použijem fallback")
        emit({
            "provider_id": "tensorx",
            "type": "api",
            "source_url": SOURCE_URL,
            "fetched_at": now_iso(),
            "models": _build_output({}),
            "warning": "Všetky URL blokové (403/chyba) — použité fallback hodnoty",
        })
        return

    soup = BeautifulSoup(html_content, "lxml")
    found: dict[str, tuple[float, float]] = {}

    # Prehľadáme tabuľky
    tables = soup.find_all("table")
    eprint(f"[TensorX] Nájdených {len(tables)} tabuliek")

    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            row_text = row.get_text(" ", strip=True)
            row_lower = row_text.lower()
            for cfg in TARGET_MODELS:
                if cfg["model_id"] in found:
                    continue
                if any(kw.lower() in row_lower for kw in cfg["search_keywords"]):
                    prices = find_price_in_row(row_text)
                    if prices:
                        found[cfg["model_id"]] = prices
                        eprint(
                            f"[TensorX] {cfg['model_id']}: "
                            f"${prices[0]}/M in, ${prices[1]}/M out (tabuľka)"
                        )

    # Prehľadáme div/li elementy
    for elem in soup.find_all(["div", "li", "tr", "td", "article", "section"]):
        elem_text = elem.get_text(" ", strip=True)
        elem_lower = elem_text.lower()
        for cfg in TARGET_MODELS:
            if cfg["model_id"] in found:
                continue
            if any(kw.lower() in elem_lower for kw in cfg["search_keywords"]):
                prices = find_price_in_row(elem_text)
                if prices:
                    found[cfg["model_id"]] = prices
                    eprint(
                        f"[TensorX] {cfg['model_id']}: "
                        f"${prices[0]}/M in, ${prices[1]}/M out (elem)"
                    )

    # Skúsime JSON vložený do stránky
    for script in soup.find_all("script"):
        if not script.string:
            continue
        try:
            # Hľadáme pole modelov s cenami
            json_match = re.search(r'\{[^<]{200,}\}', script.string)
            if json_match:
                data = json.loads(json_match.group())
                text = json.dumps(data).lower()
                for cfg in TARGET_MODELS:
                    if cfg["model_id"] in found:
                        continue
                    if any(kw.lower() in text for kw in cfg["search_keywords"]):
                        prices = find_price_in_row(json.dumps(data))
                        if prices:
                            found[cfg["model_id"]] = prices
        except (json.JSONDecodeError, TypeError):
            pass

    emit({
        "provider_id": "tensorx",
        "type": "api",
        "source_url": SOURCE_URL,
        "fetched_at": now_iso(),
        "models": _build_output(found),
    })


def _build_output(found: dict) -> list[dict]:
    result = []
    for cfg in TARGET_MODELS:
        mid = cfg["model_id"]
        prices = found.get(mid) or FALLBACK_PRICES.get(mid)
        if prices:
            result.append({
                "model_id": mid,
                "model_name": cfg["model_name"],
                "input_price_per_million_eur": prices[0],
                "output_price_per_million_eur": prices[1],
                "is_available": True,
                "note": "parsovaná zo stránky" if mid in found else "fallback",
            })
        else:
            result.append({
                "model_id": mid,
                "model_name": cfg["model_name"],
                "input_price_per_million_eur": 0,
                "output_price_per_million_eur": 0,
                "is_available": False,
                "note": "model nedostupný na TensorX",
            })
    return result


if __name__ == "__main__":
    main()
