import React from 'react';
import { ModelMatrixResult, WorkloadResults, MatrixInputs } from '../utils/calculations';
import { formatUSD, formatNumber, formatLargeNumber } from '../utils/formatters';

interface MatrixResultsProps {
  matrix: ModelMatrixResult[];
  workload: WorkloadResults;
  inputs: MatrixInputs;
}

export default function MatrixResults({ matrix, workload, inputs }: MatrixResultsProps) {
  return (
    <div className="space-y-8">
      <div className="glass-card p-6 border-l-4 border-indigo-500">
        <h2 className="text-xl font-bold text-white mb-2">Porovnávacia matica modelov</h2>
        <p className="text-sm text-slate-400">
          Tento prehľad ukazuje najvýhodnejšie API a Cloud Server riešenia pre každý z podporovaných modelov
          pri zadanej organizácii a paralelnej záťaži.
        </p>
      </div>

      {matrix.map((result) => {
        const { model, bestApi, bestGpu, bestOnPremise, winner, savings } = result;
        const winnerName = winner === 'api' ? 'Cloud API' : winner === 'gpu' ? 'Cloud Server' : 'Vlastná serverovňa';
        const winnerColor = winner === 'api' ? 'text-cyan-400' : winner === 'gpu' ? 'text-purple-400' : 'text-emerald-400';

        return (
          <div key={model.id} className="glass-card overflow-hidden">
            {/* Hlavička modelu */}
            <div 
              className="px-6 py-4 border-b border-white/5 flex items-center justify-between"
              style={{ backgroundColor: `${model.color}15` }}
            >
              <div>
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full" style={{ backgroundColor: model.color }}></span>
                  {model.name}
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  {model.totalParams}B parametrov • {model.isMoE ? 'MoE' : 'Dense'} • VRAM náročný
                  {result.gpuResults.length > 0 && ` • ${result.gpuResults[0].modelWeightVRAM_GB.toFixed(0)} GB (váhy)`}
                </p>
              </div>

              {/* Zhrnutie víťaza pre tento model */}
              <div className="text-right">
                <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Najvýhodnejšie riešenie</span>
                <p className={`text-lg font-bold ${winnerColor}`}>
                  {winnerName}
                </p>
                <p className="text-xs text-emerald-400 font-mono mt-0.5">
                  Úspora {formatUSD(savings)} / mesiac
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 divide-y lg:divide-y-0 lg:divide-x divide-white/5">
              
              {/* Ľavý stĺpec: API Možnosti */}
              <div className="p-6">
                <h4 className="text-sm font-semibold text-cyan-400 mb-4 flex items-center gap-2">
                  <span>☁️</span> Cloud API Providery
                </h4>
                
                {result.apiResults.length > 0 ? (
                  <div className="space-y-3">
                    {result.apiResults.map((api, idx) => (
                      <div key={api.provider.id} className={`p-3 rounded-lg border ${idx === 0 && winner === 'api' ? 'border-cyan-500/50 bg-cyan-500/10' : 'border-white/5 bg-white/5'}`}>
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <span className="font-semibold text-white">{api.provider.flag} {api.provider.name}</span>
                            <a href={api.provider.pricingUrl} target="_blank" rel="noreferrer" className="text-xs text-indigo-400 hover:underline ml-2">Cenník ↗</a>
                          </div>
                          <span className="font-mono font-bold text-white">{formatUSD(api.apiMonthly)}</span>
                        </div>
                        <div className="flex justify-between text-xs text-slate-400">
                          <span>{formatUSD(api.pricing.inputPricePerMillion)} in / {formatUSD(api.pricing.outputPricePerMillion)} out</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500 italic">Žiadny API provider zatiaľ nepodporuje tento model.</p>
                )}
              </div>

              {/* Pravý stĺpec: GPU Možnosti */}
              <div className="p-6">
                <h4 className="text-sm font-semibold text-purple-400 mb-4 flex items-center gap-2">
                  <span>🖥️</span> Cloud Server
                </h4>
                
                {result.gpuResults.length > 0 ? (
                  <div className="space-y-3">
                    {result.gpuResults.map((gpu, idx) => (
                      <div key={`${gpu.provider.id}-${gpu.instance.id}`} className={`p-3 rounded-lg border ${idx === 0 && winner === 'gpu' ? 'border-purple-500/50 bg-purple-500/10' : 'border-white/5 bg-white/5'}`}>
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <span className="font-semibold text-white">{gpu.provider.flag} {gpu.provider.name}</span>
                            <span className="text-xs text-slate-400 ml-2">{gpu.instance.name}</span>
                            <a href={gpu.provider.pricingUrl} target="_blank" rel="noreferrer" className="text-xs text-indigo-400 hover:underline ml-2">Cenník ↗</a>
                          </div>
                          <span className="font-mono font-bold text-white">{formatUSD(gpu.selfHostedTotal)}</span>
                        </div>
                        <div className="flex justify-between text-xs text-slate-400">
                          <span>{gpu.totalNodes} uzlov ({gpu.totalGPUs}× GPU)</span>
                        </div>
                        
                        {/* Zobrazenie debug výpočtov pre víťazný uzol */}
                        {idx === 0 && (
                          <details className="mt-4 border-t border-purple-500/30 pt-3 group">
                            <summary className="cursor-pointer text-[11px] font-semibold text-purple-400 hover:text-purple-300">Zobraziť výpočty (Debug) ▼</summary>
                            <div className="space-y-2 font-mono text-[10px] text-slate-400 mt-3 bg-slate-900/50 p-3 rounded">
                              <p>Total_Input = {formatNumber(inputs.totalMonthlyTokensM * 1_000_000)} × {inputs.inputRatio.toFixed(2)} = <span className="text-pink-400">{formatNumber(workload.totalInputTokens)}</span></p>
                              <p>Total_Output = {formatNumber(inputs.totalMonthlyTokensM * 1_000_000)} × {(1 - inputs.inputRatio).toFixed(2)} = <span className="text-pink-400">{formatNumber(workload.totalOutputTokens)}</span></p>
                              <p>Equivalent_Output_Tokens = {formatNumber(workload.totalOutputTokens)} + ({formatNumber(workload.totalInputTokens)} / 10) = <span className="text-pink-400">{formatNumber(workload.equivalentOutputTokens)}</span></p>
                              <br/>
                              <p>Working_Seconds = {inputs.workDaysPerMonth} × {inputs.hoursPerDay} × 3600 = <span className="text-pink-400">{formatNumber(workload.workingSecondsPerMonth)}</span></p>
                              <p>Avg_Equivalent_TPS = {formatNumber(workload.equivalentOutputTokens)} / {formatNumber(workload.workingSecondsPerMonth)} = <span className="text-pink-400">{Math.ceil(workload.avgEquivalentTPS).toLocaleString()}</span></p>
                              <p>Peak_TPS = ({Math.ceil(workload.avgEquivalentTPS).toLocaleString()} × {inputs.peakMultiplier}) + ({inputs.concurrentDevelopers} × 50) = <span className="text-pink-400">{Math.ceil(workload.peakTPS).toLocaleString()}</span></p>
                              <br/>
                              <p>Weights_VRAM_GB = <span className="text-cyan-400">{gpu.modelWeightVRAM_GB.toFixed(1)} GB</span></p>
                              <p>KV_Cache_VRAM = {gpu.instance.gpuCount} × {gpu.instance.vramPerGPU} × 0.15 = <span className="text-cyan-400">{gpu.totalKVCacheVRAM_GB.toFixed(1)} GB</span></p>
                              <p>Total_VRAM = {gpu.modelWeightVRAM_GB.toFixed(1)} + {gpu.totalKVCacheVRAM_GB.toFixed(1)} = <span className="text-cyan-400">{gpu.totalVRAM_GB.toFixed(1)} GB</span></p>
                              <p>Nodes_For_VRAM = ceil({gpu.totalVRAM_GB.toFixed(1)} / ({gpu.instance.gpuCount * gpu.instance.vramPerGPU} × 0.85)) = <span className="text-purple-400">{gpu.nodesForModel}</span></p>
                              <br/>
                              <p>Replicas_Needed = ceil({Math.ceil(workload.peakTPS).toLocaleString()} / {gpu.tpsPerReplica}) = <span className="text-purple-400">{gpu.replicasNeeded}</span></p>
                              <p>Total_Nodes = {gpu.nodesForModel} × {gpu.replicasNeeded} = <span className="text-emerald-400">{gpu.totalNodes}</span></p>
                              <br/>
                              {gpu.provider.id !== 'on-premise' && (
                                <>
                                  <p>Working_Hours = {inputs.workDaysPerMonth} × {inputs.hoursPerDay} = <span className="text-pink-400">{inputs.workDaysPerMonth * inputs.hoursPerDay}h</span></p>
                                  <p>Cloud_Monthly = {gpu.totalNodes} × ${gpu.instance.pricePerHour}/hr × {inputs.workDaysPerMonth * inputs.hoursPerDay}h = <span className="text-emerald-400">{formatUSD(gpu.totalNodes * gpu.instance.pricePerHour * inputs.workDaysPerMonth * inputs.hoursPerDay)}</span></p>
                                </>
                              )}
                            </div>
                          </details>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500 italic">Pre túto záťaž sa nenašla vyhovujúca GPU inštancia.</p>
                )}
              </div>

              {/* Tretí stĺpec: On-Premise Možnosti */}
              <div className="p-6">
                <h4 className="text-sm font-semibold text-emerald-400 mb-4 flex items-center gap-2">
                  <span>🏢</span> Vlastná serverovňa
                </h4>
                
                {result.onPremiseResults.length > 0 ? (
                  <div className="space-y-3">
                    {result.onPremiseResults.map((gpu, idx) => (
                      <div key={`${gpu.provider.id}-${gpu.instance.id}`} className={`p-3 rounded-lg border ${idx === 0 && winner === 'on-premise' ? 'border-emerald-500/50 bg-emerald-500/10' : 'border-white/5 bg-white/5'}`}>
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <span className="font-semibold text-white">{gpu.provider.flag} {gpu.provider.name}</span>
                            <span className="block text-xs text-slate-400">{gpu.instance.name}</span>
                          </div>
                          <span className="font-mono font-bold text-white">{formatUSD(gpu.selfHostedTotal)}</span>
                        </div>
                        <div className="flex justify-between text-xs text-slate-400 border-b border-white/5 pb-2 mb-2">
                          <span>{gpu.totalNodes} uzlov ({gpu.totalGPUs}× GPU)</span>
                        </div>
                        
                        <div className="space-y-1 font-mono text-[10px] text-slate-400">
                           <p className="flex justify-between"><span>Odpisy HW:</span> <span>{formatUSD(gpu.hardwareMonthly || 0)}</span></p>
                           <p className="flex justify-between"><span>Energie:</span> <span>{formatUSD(gpu.powerMonthly || 0)}</span></p>
                           {inputs.includeAdminSalary && <p className="flex justify-between"><span>Admin (MLOps):</span> <span>{formatUSD(gpu.adminSalary || 0)}</span></p>}
                        </div>

                        {/* Zobrazenie debug výpočtov pre víťazný uzol */}
                        {idx === 0 && (
                          <details className="mt-4 border-t border-emerald-500/30 pt-3 group">
                            <summary className="cursor-pointer text-[11px] font-semibold text-emerald-400 hover:text-emerald-300">Zobraziť výpočty (Debug) ▼</summary>
                            <div className="space-y-2 font-mono text-[10px] text-slate-400 mt-3 bg-slate-900/50 p-3 rounded">
                              <p>Nodes_For_VRAM = ceil({gpu.totalVRAM_GB.toFixed(1)} / ({gpu.instance.gpuCount * gpu.instance.vramPerGPU} × 0.85)) = <span className="text-emerald-400">{gpu.nodesForModel}</span></p>
                              <p>Replicas_Needed = ceil({Math.ceil(workload.peakTPS).toLocaleString()} / {gpu.tpsPerReplica}) = <span className="text-emerald-400">{gpu.replicasNeeded}</span></p>
                              <p>Total_Nodes = {gpu.nodesForModel} × {gpu.replicasNeeded} = <span className="text-emerald-400">{gpu.totalNodes}</span></p>
                              <br/>
                              <p>HW_Cena_Celkom = {gpu.totalNodes} × {formatUSD(gpu.instance.hardwareCostPerNode || 0)} = <span className="text-emerald-400">{formatUSD(gpu.totalNodes * (gpu.instance.hardwareCostPerNode || 0))}</span></p>
                              <p>Mesiac_Odpis = {formatUSD(gpu.totalNodes * (gpu.instance.hardwareCostPerNode || 0))} / {inputs.amortizationMonths} mesiacov = <span className="text-emerald-400">{formatUSD(gpu.hardwareMonthly || 0)}</span></p>
                            </div>
                          </details>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500 italic">Pre túto záťaž sa nenašla vyhovujúca GPU inštancia.</p>
                )}
              </div>

            </div>
          </div>
        );
      })}
    </div>
  );
}
