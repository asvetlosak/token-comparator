// ============================================================================
// constants.ts — Všetky dátové sady, modely, GPU a API providery
// ============================================================================
// Obsahuje len EU poskytovateľov s reálnymi odkazmi na cenníky.
// ============================================================================

export type Quantization = 'FP16' | 'FP8' | 'INT4';
export type GPUType = 'H100' | 'H200' | 'GB200';

export interface ModelConfig {
  id: string;
  name: string;
  totalParams: number;
  activeParams: number;
  isMoE: boolean;
  defaultQuantization: Quantization;
  contextWindow: number;
  numLayers: number;
  hiddenSize: number;
  numKVHeads: number;
  headDim: number;
  kvCacheMultiplier?: number;
  tpsPerReplica: Record<string, number>;
  color: string;
}

export interface GPUInstance {
  id: string;
  name: string;
  gpuType: GPUType;
  gpuCount: number;
  vramPerGPU: number;
  pricePerHour: number;
  pricePerMonth: number;
  hardwareCostPerNode?: number;
}

export interface GPUProvider {
  id: string;
  name: string;
  region: string;
  flag: string;
  pricingUrl: string;
  instances: GPUInstance[];
}

export interface APIModelPricing {
  modelId: string;
  modelName: string;
  inputPricePerMillion: number;
  outputPricePerMillion: number;
  isAvailable: boolean;
}

export interface APIProvider {
  id: string;
  name: string;
  region: string;
  flag: string;
  pricingUrl: string;
  models: APIModelPricing[];
}

export const BYTES_PER_PARAM: Record<Quantization, number> = {
  FP16: 2.0,
  FP8: 1.0,
  INT4: 0.5,
};

export const MODELS: ModelConfig[] = [
  {
    id: 'deepseek-v4',
    name: 'DeepSeek Pro v4 (1.6T MoE)',
    totalParams: 1600,
    activeParams: 49,
    isMoE: true,
    defaultQuantization: 'FP8',
    contextWindow: 128_000,
    numLayers: 61,
    hiddenSize: 7168,
    numKVHeads: 1,
    headDim: 576,
    tpsPerReplica: {
      H100: 2800,
      H200: 3500,
      GB200: 4800,
    },
    color: '#6366f1',
  },
  {
    id: 'minimax-m3',
    name: 'MiniMax M3 (428B MoE)',
    totalParams: 428,
    activeParams: 23,
    isMoE: true,
    defaultQuantization: 'FP8',
    contextWindow: 128_000,
    numLayers: 60,
    hiddenSize: 6144,
    numKVHeads: 4,
    headDim: 128,
    tpsPerReplica: {
      H100: 3500,
      H200: 4200,
      GB200: 5800,
    },
    color: '#f59e0b',
  },
  {
    id: 'glm-5.2',
    name: 'GLM 5.2 (744B MoE)',
    totalParams: 744,
    activeParams: 40,
    isMoE: true,
    defaultQuantization: 'FP8',
    contextWindow: 128_000,
    numLayers: 78,
    hiddenSize: 6144,
    numKVHeads: 64,
    headDim: 96,
    tpsPerReplica: {
      H100: 3200,
      H200: 4000,
      GB200: 5200,
    },
    color: '#ec4899',
  },
  {
    id: 'qwen-3.6',
    name: 'Qwen 3.6 (35B MoE)',
    totalParams: 35,
    activeParams: 3,
    isMoE: true,
    defaultQuantization: 'FP8',
    contextWindow: 128_000,
    numLayers: 40,
    hiddenSize: 2048,
    numKVHeads: 2,
    headDim: 128,
    tpsPerReplica: {
      H100: 5500,
      H200: 7000,
      GB200: 9500,
    },
    color: '#8b5cf6',
  },
];

export const GPU_PROVIDERS: GPUProvider[] = [
  {
    id: 'aws',
    name: 'AWS',
    region: 'EU (Frankfurt, Ireland)',
    flag: '🇪🇺',
    pricingUrl: 'https://aws.amazon.com/ec2/pricing/on-demand/',
    instances: [
      { id: 'aws-p5', name: 'p5.48xlarge (8x H100)', gpuType: 'H100', gpuCount: 8, vramPerGPU: 80, pricePerHour: 55.04, pricePerMonth: 55.04 * 730 },
      { id: 'aws-p5e', name: 'p5e.48xlarge (8x H200)', gpuType: 'H200', gpuCount: 8, vramPerGPU: 141, pricePerHour: 39.80, pricePerMonth: 39.80 * 730 },
    ],
  },
  {
    id: 'azure',
    name: 'Azure',
    region: 'EU (West Europe)',
    flag: '🇪🇺',
    pricingUrl: 'https://azure.microsoft.com/en-us/pricing/details/virtual-machines/linux/',
    instances: [
      { id: 'az-nd96isr', name: 'ND96isr_H100_v5 (8x H100)', gpuType: 'H100', gpuCount: 8, vramPerGPU: 80, pricePerHour: 98.32, pricePerMonth: 98.32 * 730 },
    ],
  },
  {
    id: 'verda',
    name: 'Verda',
    region: 'EU (Finland)',
    flag: '🇫🇮',
    pricingUrl: 'https://verda.com',
    instances: [
      { id: 'dc-h100-1x', name: '1x H100 SXM5', gpuType: 'H100', gpuCount: 1, vramPerGPU: 80, pricePerHour: 3.25, pricePerMonth: 3.25 * 730 },
      { id: 'dc-h100-2x', name: '2x H100 SXM5', gpuType: 'H100', gpuCount: 2, vramPerGPU: 80, pricePerHour: 6.50, pricePerMonth: 6.50 * 730 },
      { id: 'dc-h100-4x', name: '4x H100 SXM5', gpuType: 'H100', gpuCount: 4, vramPerGPU: 80, pricePerHour: 13.00, pricePerMonth: 13.00 * 730 },
      { id: 'dc-h100', name: '8x H100 SXM5', gpuType: 'H100', gpuCount: 8, vramPerGPU: 80, pricePerHour: 26.00, pricePerMonth: 26.00 * 730 },
    ],
  },
  {
    id: 'lambda',
    name: 'Lambda',
    region: 'EU (Germany)',
    flag: '🇩🇪',
    pricingUrl: 'https://lambdalabs.com/service/gpu-cloud',
    instances: [
      { id: 'lam-h100-1x', name: '1x H100 PCIe', gpuType: 'H100', gpuCount: 1, vramPerGPU: 80, pricePerHour: 3.29, pricePerMonth: 3.29 * 730 },
      { id: 'lam-h100', name: '8x H100 SXM5', gpuType: 'H100', gpuCount: 8, vramPerGPU: 80, pricePerHour: 26.32, pricePerMonth: 26.32 * 730 },
    ],
  },
  {
    id: 'nebius',
    name: 'Nebius',
    region: 'EU (Finland)',
    flag: '🇫🇮',
    pricingUrl: 'https://nebius.com/docs/compute/pricing/',
    instances: [
      { id: 'nebius-h100-1x', name: '1x H100 SXM5', gpuType: 'H100', gpuCount: 1, vramPerGPU: 80, pricePerHour: 3.85, pricePerMonth: 3.85 * 730 },
      { id: 'nebius-h100-8x', name: '8x H100 SXM5', gpuType: 'H100', gpuCount: 8, vramPerGPU: 80, pricePerHour: 30.80, pricePerMonth: 30.80 * 730 },
      { id: 'nebius-h200-8x', name: '8x H200 SXM5', gpuType: 'H200', gpuCount: 8, vramPerGPU: 141, pricePerHour: 36.00, pricePerMonth: 36.00 * 730 },
    ],
  },
  {
    id: 'ovhcloud',
    name: 'OVHcloud',
    region: 'EU (France)',
    flag: '🇫🇷',
    pricingUrl: 'https://www.ovhcloud.com/en/public-cloud/prices/',
    instances: [
      { id: 'ovh-h100-8x', name: '8x H100 SXM5', gpuType: 'H100', gpuCount: 8, vramPerGPU: 80, pricePerHour: 26.24, pricePerMonth: 26.24 * 730 },
    ],
  },
  {
    id: 'on-premise',
    name: 'Vlastná serverovňa (Nákup)',
    region: 'Local',
    flag: '🏢',
    pricingUrl: 'https://smicro.sk',
    instances: [
      { id: 'smicro-dgx-h200', name: 'NVIDIA DGX H200 8x 141GB', gpuType: 'H200', gpuCount: 8, vramPerGPU: 141, pricePerHour: 0, pricePerMonth: 0, hardwareCostPerNode: 397992 },
      { id: 'smicro-dgx-b200', name: 'NVIDIA DGX B200 8x 180GB', gpuType: 'H200', gpuCount: 8, vramPerGPU: 180, pricePerHour: 0, pricePerMonth: 0, hardwareCostPerNode: 379546 },
    ],
  },
];

export const API_PROVIDERS: APIProvider[] = [
  {
    id: 'nebius-api',
    name: 'Nebius Token Factory',
    region: 'EU (Finland)',
    flag: '🇫🇮',
    pricingUrl: 'https://tokenfactory.nebius.com/models',
    models: [
      { modelId: 'deepseek-v4', modelName: 'DeepSeek Pro v4', inputPricePerMillion: 1.75, outputPricePerMillion: 3.50, isAvailable: true },
      { modelId: 'glm-5.2', modelName: 'GLM 5.2', inputPricePerMillion: 1.40, outputPricePerMillion: 4.40, isAvailable: true },
      { modelId: 'minimax-m3', modelName: 'MiniMax M3', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
      { modelId: 'qwen-3.6', modelName: 'Qwen 3.6', inputPricePerMillion: 0.60, outputPricePerMillion: 3.60, isAvailable: true },
    ],
  },
  {
    id: 'scaleway',
    name: 'Scaleway',
    region: 'EU (France/Netherlands)',
    flag: '🇪🇺',
    pricingUrl: 'https://www.scaleway.com/en/pricing/?tags=ai',
    models: [
      { modelId: 'deepseek-v4', modelName: 'DeepSeek Pro v4', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
      { modelId: 'glm-5.2', modelName: 'GLM 5.2', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
      { modelId: 'minimax-m3', modelName: 'MiniMax M3', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
      { modelId: 'qwen-3.6', modelName: 'Qwen 3.6', inputPricePerMillion: 0.072, outputPricePerMillion: 0.464, isAvailable: true },
    ],
  },
  {
    id: 'greenpt-api',
    name: 'GreenPT',
    region: 'EU (Netherlands)',
    flag: '🇳🇱',
    pricingUrl: 'https://greenpt.com/pricing',
    models: [
      { modelId: 'deepseek-v4', modelName: 'DeepSeek Pro v4', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
      { modelId: 'glm-5.2', modelName: 'GLM 5.2', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
      { modelId: 'minimax-m3', modelName: 'MiniMax M3', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
      { modelId: 'qwen-3.6', modelName: 'Qwen 3.6', inputPricePerMillion: 0.072, outputPricePerMillion: 0.464, isAvailable: true },
    ],
  },
  {
    id: 'tensorx',
    name: 'TensorX',
    region: 'EU (Sweden)',
    flag: '🇸🇪',
    pricingUrl: 'https://tensorx.ai/models/',
    models: [
      { modelId: 'deepseek-v4', modelName: 'DeepSeek Pro v4', inputPricePerMillion: 1.75, outputPricePerMillion: 3.50, isAvailable: true },
      { modelId: 'glm-5.2', modelName: 'GLM 5.2', inputPricePerMillion: 1.50, outputPricePerMillion: 4.50, isAvailable: true },
      { modelId: 'minimax-m3', modelName: 'MiniMax M3', inputPricePerMillion: 0.40, outputPricePerMillion: 2.00, isAvailable: true },
      { modelId: 'qwen-3.6', modelName: 'Qwen 3.6', inputPricePerMillion: 0.06, outputPricePerMillion: 0.25, isAvailable: true },
    ],
  },
  {
    id: 'aws-bedrock-api',
    name: 'AWS Bedrock',
    region: 'EU (Frankfurt, Paris)',
    flag: '🇪🇺',
    pricingUrl: 'https://aws.amazon.com/bedrock/pricing/',
    models: [
      { modelId: 'deepseek-v4', modelName: 'DeepSeek Pro v4', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
      { modelId: 'glm-5.2', modelName: 'GLM 5.2', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
      { modelId: 'minimax-m3', modelName: 'MiniMax M3', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
      { modelId: 'qwen-3.6', modelName: 'Qwen 3.6', inputPricePerMillion: 0.072, outputPricePerMillion: 0.464, isAvailable: true },
    ],
  },
  {
    id: 'inceptron-api',
    name: 'Inceptron',
    region: 'EU (Sweden)',
    flag: '🇸🇪',
    pricingUrl: 'https://www.inceptron.io/pricing',
    models: [
      { modelId: 'deepseek-v4', modelName: 'DeepSeek Pro v4', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
      { modelId: 'glm-5.2', modelName: 'GLM 5.2', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
      { modelId: 'minimax-m3', modelName: 'MiniMax M3', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
      { modelId: 'qwen-3.6', modelName: 'Qwen 3.6', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
    ],
  },
  {
    id: 'infercom-api',
    name: 'Infercom',
    region: 'EU (Luxembourg)',
    flag: '🇱🇺',
    pricingUrl: 'https://infercom.ai/pricing/',
    models: [
      { modelId: 'deepseek-v4', modelName: 'DeepSeek Pro v4', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
      { modelId: 'glm-5.2', modelName: 'GLM 5.2', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
      { modelId: 'minimax-m3', modelName: 'MiniMax M3', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
      { modelId: 'qwen-3.6', modelName: 'Qwen 3.6', inputPricePerMillion: 0, outputPricePerMillion: 0, isAvailable: false },
    ],
  }
];

export const DEFAULTS = {
  totalMonthlyTokensM: 25000,
  concurrentDevelopers: 30,
  inputRatio: 0.54,
  workDaysPerMonth: 21,
  hoursPerDay: 10,
  peakMultiplier: 1.5,
  includeAdminSalary: false,
  adminSalaryPerMonth: 10000,
  amortizationMonths: 24,
  powerCostPerNodePerMonth: 1500,
  avgContextLength: 8192,
  quantization: 'FP8' as Quantization,
};
