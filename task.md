# Implementácia On-Premise (Vlastná serverovňa)

- `[x]` 1. Úprava `constants.ts`
  - Pridať `amortizationMonths` (default 12) a `powerCostPerNodePerMonth` (default 1500) do `DEFAULTS`.
  - Pridať nového providera `on-premise` (Vlastná serverovňa) do zoznamu `GPU_PROVIDERS` s inštanciami H100 a H200, ktoré budú mať nastavené ceny z `smicro.sk` namiesto hodinovej sadzby.
  
- `[x]` 2. Úprava `calculations.ts`
  - Rozšíriť `MatrixInputs` o `amortizationMonths` a `powerCostPerNodePerMonth`.
  - Rozšíriť logiku `calculateWorkload` alebo priamo `calculateMatrix` o On-Premise kalkuláciu, ktorá počíta s hardvérovou cenou, elektrinou a platmi namiesto hodinovej cloudovej sadzby.
  - Vrátiť zoznam `onPremiseResults` v `ModelMatrixResult`.

- `[x]` 3. Úprava `InputPanel.tsx`
  - Pridať slider `Doba odpisovania HW (mesiace)` s min 12 a max 60.

- `[x]` 4. Úprava `MatrixResults.tsx`
  - Zmeniť dizajn výsledkovej matice tak, aby zobrazovala **3 stĺpce** (Cloud API, Cloud Server, Vlastná serverovňa).
  - Určiť najvýhodnejšie riešenie z týchto troch možností a zobraziť úsporu.
  - Pre On-Premise možnosť vyrenderovať dropdown s "Zobraziť výpočty (Debug)", kde budú rozpísané vzorce pre CAPEX, amortizáciu a OPEX.

- `[x]` 5. Úprava `CalculationDetails.tsx`
  - Rozšíriť metodiku o krok pre "Vlastnú serverovňu (On-Premise)" a vysvetliť vzorce výpočtu.
