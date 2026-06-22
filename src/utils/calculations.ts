// ============================================================================
// calculations.ts — Výpočtové jadro TCO kalkulačky
// ============================================================================
// Obsahuje funkcie na výpočet základných parametrov záťaže (TPS, VRAM)
// a novú funkciu pre maticové porovnanie všetkých scenárov.
// ============================================================================

import {
  MODELS,
  GPU_PROVIDERS,
  API_PROVIDERS,
  type ModelConfig,
  type GPUProvider,
  type GPUInstance,
  type APIProvider,
  type APIModelPricing,
  type GPUType,
  type Quantization,
  BYTES_PER_PARAM,
} from '../data/constants';

// ---------------------------------------------------------------------------
// Vstupné parametre (len spoločné parametre, výber z UI)
// ---------------------------------------------------------------------------
export interface MatrixInputs {
  totalMonthlyTokensM: number;
  concurrentDevelopers: number;
  inputRatio: number;
  workDaysPerMonth: number;
  hoursPerDay: number;
  peakMultiplier: number;
  includeAdminSalary: boolean;
  adminSalaryPerMonth: number;
  amortizationMonths: number;
  powerCostPerNodePerMonth: number;
  avgContextLength: number;
  quantization: Quantization;
}

// ---------------------------------------------------------------------------
// Spoločné výsledky pre záťaž (TPS, tokeny)
// ---------------------------------------------------------------------------
export interface WorkloadResults {
  totalMonthlyTokens: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  workingSecondsPerMonth: number;
  avgTPS: number;
  equivalentOutputTokens: number;
  avgEquivalentTPS: number;
  peakTPS: number;
  estimatedConcurrency: number;
}

// ---------------------------------------------------------------------------
// Výsledky pre konkrétny GPU scenár
// ---------------------------------------------------------------------------
export interface GPUResult {
  provider: GPUProvider;
  instance: GPUInstance;
  modelWeightVRAM_GB: number;
  kvCachePerRequest_GB: number;
  totalKVCacheVRAM_GB: number;
  totalVRAM_GB: number;
  vramPerNode_GB: number;
  nodesForModel: number;
  tpsPerReplica: number;
  replicasNeeded: number;
  totalNodes: number;
  totalGPUs: number;
  selfHostedTotal: number;
  hardwareMonthly?: number;
  powerMonthly?: number;
  adminSalary?: number;
}

// ---------------------------------------------------------------------------
// Výsledky pre konkrétny API scenár
// ---------------------------------------------------------------------------
export interface APIResult {
  provider: APIProvider;
  pricing: APIModelPricing;
  inputCost: number;
  outputCost: number;
  apiMonthly: number;
}

// ---------------------------------------------------------------------------
// Výsledky pre jeden model v matici
// ---------------------------------------------------------------------------
export interface ModelMatrixResult {
  model: ModelConfig;
  apiResults: APIResult[];
  gpuResults: GPUResult[];
  onPremiseResults: GPUResult[];
  winner: 'api' | 'gpu' | 'on-premise';
  bestApi?: APIResult;
  bestGpu?: GPUResult;
  bestOnPremise?: GPUResult;
  savings: number; // Kladné číslo (rozdiel medzi druhým a víťazom)
}

// ---------------------------------------------------------------------------
// Krok 1: Výpočet základnej záťaže (Workload) - nezávisí od modelu
// ---------------------------------------------------------------------------
export function calculateWorkload(inputs: MatrixInputs): WorkloadResults {
  const totalMonthlyTokens = inputs.totalMonthlyTokensM * 1_000_000;
  const totalInputTokens = totalMonthlyTokens * inputs.inputRatio;
  const totalOutputTokens = totalMonthlyTokens * (1 - inputs.inputRatio);

  const workingSecondsPerMonth = inputs.workDaysPerMonth * inputs.hoursPerDay * 3600;
  
  // Hrubé priemerné TPS (všetky tokeny dokopy)
  const avgTPS = totalMonthlyTokens / workingSecondsPerMonth;
  
  // Efektívne TPS pre dimenzovanie hardvéru:
  // Input tokeny (Prefill) sa spracovávajú v batchoch oveľa rýchlejšie než Output tokeny (Decode).
  // Typický pomer na moderných GPU je ~10:1 (Prefill je 10x rýchlejší).
  const equivalentOutputTokens = totalOutputTokens + (totalInputTokens / 10);
  const avgEquivalentTPS = equivalentOutputTokens / workingSecondsPerMonth;

  const estimatedConcurrency = inputs.concurrentDevelopers;
  
  // Peak TPS zohľadňuje priemernú záťaž so špičkovým násobiteľom (objemová zložka),
  // ku ktorej sa pripočítava paralelná zložka: každý paralelný developer vyžaduje rezervu napr. 50 TPS
  const peakTPS = (avgEquivalentTPS * inputs.peakMultiplier) + (estimatedConcurrency * 50);

  return {
    totalMonthlyTokens,
    totalInputTokens,
    totalOutputTokens,
    workingSecondsPerMonth,
    avgTPS,
    equivalentOutputTokens,
    avgEquivalentTPS,
    peakTPS,
    estimatedConcurrency,
  };
}

// ---------------------------------------------------------------------------
// Krok 2: Výpočet pre jeden GPU scenár
// ---------------------------------------------------------------------------
function calculateGPUInstance(
  inputs: MatrixInputs,
  workload: WorkloadResults,
  provider: GPUProvider,
  instance: GPUInstance,
  model: ModelConfig
): GPUResult | null {
  const bytesPerParam = BYTES_PER_PARAM[inputs.quantization];

  // VRAM model weights
  const modelWeightVRAM_GB = (model.totalParams * 1e9 * bytesPerParam) / (1024 ** 3);

  // VRAM KV cache - fixne alokujeme 15% z celkovej teoretickej kapacity GPU uzla
  const instanceVramTotal = instance.gpuCount * instance.vramPerGPU;
  const totalKVCacheVRAM_GB = instanceVramTotal * 0.15;
  const kvCachePerRequest_GB = 0;

  // Total VRAM
  const totalVRAM_GB = modelWeightVRAM_GB + totalKVCacheVRAM_GB;

  // Sizing
  const vramPerNode_GB = instance.gpuCount * instance.vramPerGPU;
  const nodesForModel = Math.max(1, Math.ceil(totalVRAM_GB / (vramPerNode_GB * 0.85)));

  // TPS a Overhead
  const tpsPerReplicaRaw = model.tpsPerReplica[instance.gpuType];
  if (!tpsPerReplicaRaw) return null; 
  
  const tpsPerReplica = tpsPerReplicaRaw;
  const replicasNeeded = Math.max(1, Math.ceil(workload.peakTPS / tpsPerReplica));
  const totalNodes = nodesForModel * replicasNeeded;
  const totalGPUs = totalNodes * instance.gpuCount;

  let hardwareMonthly = 0;
  let powerMonthly = 0;
  const adminSalary = inputs.includeAdminSalary ? inputs.adminSalaryPerMonth : 0;

  // Pracovné hodiny za mesiac (Scale-to-Zero: platíš len keď bežia)
  const workingHoursPerMonth = inputs.workDaysPerMonth * inputs.hoursPerDay;

  if (provider.id === 'on-premise' && instance.hardwareCostPerNode) {
    // On-premise: HW amortizácia a energia bežia 24/7, nezávisle od vyťaženia
    hardwareMonthly = (totalNodes * instance.hardwareCostPerNode) / inputs.amortizationMonths;
    powerMonthly = totalNodes * inputs.powerCostPerNodePerMonth;
  } else {
    // Cloud: platíš za skutočné pracovné hodiny (Scale-to-Zero mimo pracovnej doby)
    hardwareMonthly = totalNodes * instance.pricePerHour * workingHoursPerMonth;
  }

  const selfHostedTotal = hardwareMonthly + powerMonthly + adminSalary;

  return {
    provider,
    instance,
    modelWeightVRAM_GB,
    kvCachePerRequest_GB,
    totalKVCacheVRAM_GB,
    totalVRAM_GB,
    vramPerNode_GB,
    nodesForModel,
    tpsPerReplica,
    replicasNeeded,
    totalNodes,
    totalGPUs,
    selfHostedTotal,
    hardwareMonthly,
    powerMonthly,
    adminSalary
  };
}

// ---------------------------------------------------------------------------
// Krok 3: Výpočet pre jeden API scenár
// ---------------------------------------------------------------------------
function evaluateAPI(
  inputs: MatrixInputs,
  workload: WorkloadResults,
  provider: APIProvider,
  pricing: APIModelPricing
): APIResult | null {
  if (!pricing.isAvailable) return null;

  const inputCost = (workload.totalInputTokens / 1_000_000) * pricing.inputPricePerMillion;
  const outputCost = (workload.totalOutputTokens / 1_000_000) * pricing.outputPricePerMillion;
  const apiMonthly = inputCost + outputCost;

  return {
    provider,
    pricing,
    inputCost,
    outputCost,
    apiMonthly,
  };
}

// ---------------------------------------------------------------------------
// Krok 4: Hlavná maticová funkcia
// ---------------------------------------------------------------------------
export function calculateMatrix(inputs: MatrixInputs): {
  workload: WorkloadResults;
  matrix: ModelMatrixResult[];
} {
  const workload = calculateWorkload(inputs);
  const matrix: ModelMatrixResult[] = [];

  for (const model of MODELS) {
    const gpuResults: GPUResult[] = [];
    const onPremiseResults: GPUResult[] = [];
    const apiResults: APIResult[] = [];

    GPU_PROVIDERS.forEach((provider) => {
      provider.instances.forEach((instance) => {
        const res = calculateGPUInstance(inputs, workload, provider, instance, model);
        if (res) {
          if (provider.id === 'on-premise') {
            onPremiseResults.push(res);
          } else {
            gpuResults.push(res);
          }
        }
      });
    });

    gpuResults.sort((a, b) => a.selfHostedTotal - b.selfHostedTotal);
    onPremiseResults.sort((a, b) => a.selfHostedTotal - b.selfHostedTotal);

    for (const provider of API_PROVIDERS) {
      const pricing = provider.models.find(m => m.modelId === model.id);
      if (pricing) {
        const res = evaluateAPI(inputs, workload, provider, pricing);
        if (res) apiResults.push(res);
      }
    }
    apiResults.sort((a, b) => a.apiMonthly - b.apiMonthly);

    // 3. Nájdi víťaza
    const bestGpu = gpuResults[0];
    const bestApi = apiResults[0];
    const bestOnPremise = onPremiseResults[0];
    
    // Porovnáme tri najlepšie ceny
    const costs = [
      { type: 'api' as const, cost: bestApi ? bestApi.apiMonthly : Infinity },
      { type: 'gpu' as const, cost: bestGpu ? bestGpu.selfHostedTotal : Infinity },
      { type: 'on-premise' as const, cost: bestOnPremise ? bestOnPremise.selfHostedTotal : Infinity }
    ];
    
    costs.sort((a, b) => a.cost - b.cost);
    
    const winner = costs[0].cost !== Infinity ? costs[0].type : 'api';
    const savings = costs[1].cost !== Infinity ? (costs[1].cost - costs[0].cost) : 0;

    matrix.push({
      model,
      apiResults,
      gpuResults,
      onPremiseResults,
      winner,
      bestApi,
      bestGpu,
      bestOnPremise,
      savings
    });
  }

  return { workload, matrix };
}
