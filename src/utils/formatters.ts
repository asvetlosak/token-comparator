// ============================================================================
// formatters.ts — Pomocné funkcie na formátovanie čísel a hodnôt
// ============================================================================

/** Formátuje číslo ako USD menu s tisíckovými oddeľovačmi */
export function formatUSD(value: number): string {
  if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(2)}M`;
  }
  
  const decimals = value < 100 ? 2 : 0;
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: value < 1 ? 3 : decimals, // Pre ceny pod 1$ (napr. 0.06) povolíme aj 3 desatinné miesta
  }).format(value);
}

/** Formátuje veľké číslo s postfixom (K, M, B) */
export function formatLargeNumber(value: number): string {
  if (value >= 1e12) return `${(value / 1e12).toFixed(1)}T`;
  if (value >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
  return value.toFixed(0);
}

/** Formátuje číslo s tisíckovými oddeľovačmi */
export function formatNumber(value: number, decimals = 0): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/** Formátuje GB hodnotu */
export function formatGB(value: number): string {
  if (value >= 1024) {
    return `${(value / 1024).toFixed(1)} TB`;
  }
  return `${value.toFixed(0)} GB`;
}

/** Formátuje percentá */
export function formatPercent(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
}

/** Formátuje TPS */
export function formatTPS(value: number): string {
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K tok/s`;
  }
  return `${value.toFixed(0)} tok/s`;
}
