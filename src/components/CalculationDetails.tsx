import React from 'react';
import { MODELS, GPU_PROVIDERS, API_PROVIDERS, GPU_HARDWARE_SPECS } from '../data/constants';

export default function CalculationDetails() {
  return (
    <div className="space-y-6">
      <div className="glass-card p-6 border-l-4 border-purple-500">
        <h2 className="text-xl font-bold text-white mb-2">Metodika výpočtov a Zdroje dát</h2>
        <p className="text-sm text-slate-400">
          Kalkulačka používa 4-krokový model pre odhad infraštruktúry a nákladov. 
          Všetky údaje sú odhadované na základe verejne dostupných cenníkov (Q2 2025).
        </p>
      </div>

      <div className="space-y-4">
        {/* Krok 0: Zdroje dát */}
        <details className="glass-card rounded-lg group" open>
          <summary className="px-6 py-4 cursor-pointer font-semibold text-white flex items-center justify-between hover:bg-white/5 transition-colors">
            <div className="flex items-center gap-3">
              <span className="flex items-center justify-center w-6 h-6 rounded bg-slate-800 text-slate-400 text-xs font-mono">0</span>
              Zdroje dát a Cenníky
            </div>
            <span className="text-slate-500 group-open:rotate-180 transition-transform">▼</span>
          </summary>
          <div className="px-6 pb-6 pt-2 border-t border-white/5 space-y-6">
            <div>
              <h4 className="text-sm font-semibold text-cyan-400 mb-3">API Providery (Cenníky)</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {API_PROVIDERS.map(p => (
                  <div key={p.id} className="p-3 rounded bg-slate-900 border border-slate-800 flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-slate-200">{p.flag} {p.name}</span>
                      <a href={p.pricingUrl} target="_blank" rel="noreferrer" className="text-xs text-indigo-400 hover:underline">Zdroj ↗</a>
                    </div>
                    <div className="space-y-1 mt-2 border-t border-slate-800 pt-2">
                      {p.models.filter(m => m.isAvailable).map(m => (
                        <div key={m.modelId} className="flex justify-between text-xs text-slate-400">
                          <span>{m.modelName}</span>
                          <span className="font-mono text-cyan-400">{m.inputPricePerMillion} / {m.outputPricePerMillion} €</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-purple-400 mb-3">GPU Cloud Providery (Cenníky)</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {GPU_PROVIDERS.map(p => (
                  <div key={p.id} className="p-3 rounded bg-slate-900 border border-slate-800 flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-slate-200">{p.flag} {p.name}</span>
                      <a href={p.pricingUrl} target="_blank" rel="noreferrer" className="text-xs text-indigo-400 hover:underline">Zdroj ↗</a>
                    </div>
                    <div className="space-y-1 mt-2 border-t border-slate-800 pt-2">
                      {p.instances.map(inst => {
                        const isPurchase = inst.pricePerHour === 0 && inst.hardwareCostPerNode;
                        const priceText = isPurchase ? `${inst.hardwareCostPerNode?.toLocaleString()} €` : `${inst.pricePerHour.toFixed(2)} €/h`;
                        
                        return (
                          <div key={inst.id} className="flex justify-between items-center text-xs text-slate-400 gap-2">
                            <div className="flex gap-1 items-center truncate">
                              <span className="truncate" title={inst.name}>{inst.name}</span>
                              {inst.itemUrl && (
                                <a href={inst.itemUrl} target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline shrink-0" title="Zobraziť v e-shope">↗</a>
                              )}
                            </div>
                            <span className="font-mono text-purple-400 whitespace-nowrap">{priceText}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-2 border-t border-white/5 pt-6">
              <h4 className="text-sm font-semibold text-emerald-400 mb-2">Hardvérové Benchmarky a Konštanty</h4>
              <div className="bg-slate-900 p-4 rounded-lg border border-slate-800 text-sm text-slate-300">
                <p className="mb-4">
                  Priepustnosť jednotlivých modelov (TPS) a iné premenné vo výpočte vychádzajú zo zverejnených výkonnostných benchmarkov optimalizovaných inferenčných enginov (ako <strong>vLLM</strong> a <strong>TensorRT-LLM</strong>).
                </p>
                <ul className="list-disc list-inside space-y-1 text-slate-400 mb-4">
                  <li>
                    <strong>Zdroje dát:</strong>{' '}
                    <a href="https://github.com/vllm-project/vllm/releases" target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline">vLLM Performance Benchmarks</a>,{' '}
                    <a href="https://nvidia.github.io/TensorRT-LLM/performance.html" target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline">NVIDIA TensorRT-LLM Docs</a>.
                  </li>
                  <li><strong>VRAM Limit (0.85):</strong> Kalkulačka bezpečne alokuje maximálne 85% fyzickej pamäte GPU, zvyšných 15% ostáva ako rezerva pre OS a CUDA runtime.</li>
                  <li><strong>Kvantizácia (Bytes_Per_Param):</strong> FP8 = 1 byte/param, INT4 = 0.5 byte/param. Určuje presnú veľkosť statických váh modelu.</li>
                </ul>
                
                <h5 className="font-semibold text-emerald-500 mb-2 mt-4 border-t border-slate-800 pt-4">Hardvérový Výkon (GPU_HARDWARE_SPECS) a Koeficienty</h5>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-800 text-slate-300">
                      <tr>
                        <th className="px-3 py-2 rounded-tl">Karta</th>
                        <th className="px-3 py-2">Bandwidth (GB/s)</th>
                        <th className="px-3 py-2">Výkon (TFLOPS)</th>
                        <th className="px-3 py-2 rounded-tr">Výkonnostný koeficient</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 text-slate-400">
                      {Object.entries(GPU_HARDWARE_SPECS).map(([gpu, specs]) => {
                        const base = GPU_HARDWARE_SPECS['H100'];
                        const ratio = (0.8 * (specs.memoryBandwidthGBs / base.memoryBandwidthGBs)) + (0.2 * (specs.tflops / base.tflops));
                        return (
                          <tr key={gpu} className="hover:bg-slate-800/50">
                            <td className="px-3 py-2 text-slate-200 font-medium">{gpu}</td>
                            <td className="px-3 py-2 font-mono text-emerald-400">{specs.memoryBandwidthGBs.toLocaleString()}</td>
                            <td className="px-3 py-2 font-mono text-emerald-400">{specs.tflops.toLocaleString()}</td>
                            <td className="px-3 py-2 font-mono text-purple-400">{ratio.toFixed(3)}x</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                <h5 className="font-semibold text-cyan-500 mb-2 mt-4 border-t border-slate-800 pt-4">Základná priepustnosť na uzol H100 (Baseline TPS)</h5>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-800 text-slate-300">
                      <tr>
                        <th className="px-3 py-2 rounded-tl">Model</th>
                        <th className="px-3 py-2 rounded-tr">Base H100 TPS (1 Uzol / 8 kariet)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 text-slate-400">
                      {MODELS.map(m => (
                        <tr key={m.id} className="hover:bg-slate-800/50">
                          <td className="px-3 py-2 text-slate-200 font-medium">{m.name}</td>
                          <td className="px-3 py-2 font-mono text-emerald-400">{m.tpsPerReplica.H100 ? m.tpsPerReplica.H100.toLocaleString() : '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </details>

        {/* Krok 1: TPS */}
        <details className="glass-card rounded-lg group" open>
          <summary className="px-6 py-4 cursor-pointer font-semibold text-white flex items-center justify-between hover:bg-white/5 transition-colors">
            <div className="flex items-center gap-3">
              <span className="flex items-center justify-center w-6 h-6 rounded bg-indigo-500/20 text-indigo-400 text-xs font-mono border border-indigo-500/30">1</span>
              Výpočet priepustnosti (TPS)
            </div>
            <span className="text-slate-500 group-open:rotate-180 transition-transform">▼</span>
          </summary>
          <div className="px-6 pb-6 pt-2 border-t border-white/5 space-y-4">
            <div className="bg-slate-900 p-4 rounded-lg font-mono text-xs text-slate-300 space-y-2 border border-slate-800">
              <p><span className="text-pink-400">Total_Input</span> = Tokens_M × 1,000,000 × Input_Ratio</p>
              <p><span className="text-pink-400">Total_Output</span> = Tokens_M × 1,000,000 × (1 - Input_Ratio)</p>
              <p className="text-slate-500 pt-2 border-t border-slate-800 mt-2">
                // Input tokeny (Prefill) sa spracujú ~10x rýchlejšie než Output tokeny (Decode).
              </p>
              <p><span className="text-pink-400">Equivalent_Output_Tokens</span> = Total_Output + (Total_Input / 10)</p>
              <br/>
              <p><span className="text-pink-400">Working_Seconds</span> = Days × Hours × 3600</p>
              <p><span className="text-pink-400">Avg_Equivalent_TPS</span> = Equivalent_Output_Tokens / Working_Seconds</p>
              <p className="text-slate-500 pt-2 border-t border-slate-800 mt-2">
                // Peak TPS zohľadňuje priemernú záťaž a dávkové vyťaženie (Multiplier)
              </p>
              <p><span className="text-pink-400">Peak_TPS</span> = Avg_Equivalent_TPS × Peak_Multiplier</p>
            </div>
          </div>
        </details>

        {/* Krok 2: VRAM */}
        <details className="glass-card rounded-lg group" open>
          <summary className="px-6 py-4 cursor-pointer font-semibold text-white flex items-center justify-between hover:bg-white/5 transition-colors">
            <div className="flex items-center gap-3">
              <span className="flex items-center justify-center w-6 h-6 rounded bg-indigo-500/20 text-indigo-400 text-xs font-mono border border-indigo-500/30">2</span>
              Výpočet VRAM (Váhy + KV Cache)
            </div>
            <span className="text-slate-500 group-open:rotate-180 transition-transform">▼</span>
          </summary>
          <div className="px-6 pb-6 pt-2 border-t border-white/5 space-y-4">
            <div className="bg-slate-900 p-4 rounded-lg font-mono text-xs text-slate-300 space-y-2 border border-slate-800">
              <p className="text-slate-500">// 1. VRAM pre model (závisí od kvantizácie, FP8 = 1 byte/param)</p>
              <p><span className="text-cyan-400">Weights_VRAM</span> = Total_Params × Bytes_Per_Param</p>
              <br/>
              <p className="text-slate-500">// 2. KV Cache pre maximálny priepustný batching (flat 15% z kapacity servera)</p>
              <p><span className="text-cyan-400">KV_Cache_VRAM</span> = Node_GPU_Count × GPU_VRAM × 0.15</p>
              <br/>
              <p className="text-slate-500">// 3. Celková alokovaná VRAM</p>
              <p><span className="text-cyan-400">Total_VRAM</span> = Weights_VRAM + KV_Cache_VRAM</p>
            </div>
          </div>
        </details>

        {/* Krok 3: Sizing */}
        <details className="glass-card rounded-lg group" open>
          <summary className="px-6 py-4 cursor-pointer font-semibold text-white flex items-center justify-between hover:bg-white/5 transition-colors">
            <div className="flex items-center gap-3">
              <span className="flex items-center justify-center w-6 h-6 rounded bg-indigo-500/20 text-indigo-400 text-xs font-mono border border-indigo-500/30">3</span>
              Dimenzovanie Infraštruktúry a Príklad (MiniMax M3)
            </div>
            <span className="text-slate-500 group-open:rotate-180 transition-transform">▼</span>
          </summary>
          <div className="px-6 pb-6 pt-2 border-t border-white/5 space-y-4">
            <div className="bg-slate-900 p-4 rounded-lg font-mono text-xs text-slate-300 space-y-2 border border-slate-800 mb-4">
              <p className="text-slate-500">// 1. Koľko uzlov potrebujeme na VRAM (na uzle sa využije max 85% pamäte)</p>
              <p><span className="text-purple-400">Nodes_For_VRAM</span> = ceil(Total_VRAM / (Node_VRAM × 0.85))</p>
              <br/>
              <p className="text-slate-500">// 2. Koľko takýchto replík potrebujeme pre TPS</p>
              <p><span className="text-purple-400">Replicas_Needed</span> = ceil(Peak_TPS / TPS_Per_Replica)</p>
            </div>
            
            <div className="p-4 bg-indigo-900/30 border border-indigo-500/30 rounded-lg text-sm text-slate-300">
              <h5 className="font-bold text-indigo-400 mb-2">Príklad pre MiniMax M3 (428B MoE) v FP8 na inštancii 8x H100</h5>
              <ul className="list-disc list-inside space-y-1">
                <li><strong>Weights_VRAM:</strong> 428B parametrov × 1 byte = <span className="font-mono text-cyan-300">428 GB</span></li>
                <li><strong>KV_Cache:</strong> 8x H100 = 640 GB kapacity. Z toho 15% pre KV = <span className="font-mono text-cyan-300">96 GB</span></li>
                <li><strong>Total_VRAM:</strong> 428 + 96 = <span className="font-mono text-cyan-300">524 GB</span></li>
                <li><strong>Nodes_For_VRAM:</strong> Uzol 8x H100 má využiteľných 85% (544 GB). Teda <span className="font-mono text-purple-300">524 GB / 544 GB = 1 Uzol</span> (kvôli pamäti)</li>
                <li><strong>Replicas_Needed:</strong> Kalkulačka volí kapacitu na základe celkového mesačného <em>ekvivalentného</em> objemu. Ak má používateľ zadaných extrémych 25 miliárd tokenov/mesiac, no 80% z toho sú len Input tokeny (čítanie kontextu je bleskové), systém prepočíta túto masu na Equivalent Output TPS. Odhadovaný Peak_TPS tak dramaticky klesne (napr. na ~14 000 TPS) a namiesto nezmyselných 15 uzlov kalkulačka alokuje rozumné <span className="font-mono text-purple-300">ceil(14000 / 3800) = 4 repliky</span>.</li>
                <li><strong>Záver:</strong> Na bežnú prevádzku MiniMax M3 stačí 1 GPU uzol (8x H100). Ak zadáte extrémny "Počet tokenov", systém pridá ďalšie uzly, pričom zohľadňuje obrovskú rýchlosť čítania (Prefill) vs. pomalšie generovanie (Decode).</li>
              </ul>
            </div>
          </div>
        </details>

        {/* Krok 4: Náklady */}
        <details className="glass-card rounded-lg group" open>
          <summary className="px-6 py-4 cursor-pointer font-semibold text-white flex items-center justify-between hover:bg-white/5 transition-colors">
            <div className="flex items-center gap-3">
              <span className="flex items-center justify-center w-6 h-6 rounded bg-indigo-500/20 text-indigo-400 text-xs font-mono border border-indigo-500/30">4</span>
              Výpočet nákladov na Cloud Server (On-Demand)
            </div>
            <span className="text-slate-500 group-open:rotate-180 transition-transform">▼</span>
          </summary>
          <div className="px-6 pb-6 pt-2 border-t border-white/5 space-y-4">
            <div className="bg-slate-900 p-4 rounded-lg font-mono text-xs text-slate-300 space-y-2 border border-slate-800">
              <p className="text-slate-500">// Kalkulačka predpokladá Scale-to-Zero: GPU uzly bežia len počas pracovnej doby.</p>
              <p className="text-slate-500">// Mimo pracovných hodín a víkendov sa vypínajú — platí sa len za skutočné hodiny.</p>
              <br/>
              <p><span className="text-pink-400">Working_Hours</span> = Work_Days × Hours_Per_Day</p>
              <p><span className="text-pink-400">Monthly_Cloud_Cost</span> = Total_Nodes × Price_Per_Hour × Working_Hours</p>
              <p><span className="text-pink-400">MLOps_Admin</span> = IncludeAdmin ? AdminSalary : 0</p>
              <p><span className="text-emerald-400 font-bold">Cloud_Server_Total</span> = Monthly_Cloud_Cost + MLOps_Admin</p>
            </div>
          </div>
        </details>

        {/* Krok 5: On-Premise Náklady */}
        <details className="glass-card rounded-lg group" open>
          <summary className="px-6 py-4 cursor-pointer font-semibold text-white flex items-center justify-between hover:bg-white/5 transition-colors">
            <div className="flex items-center gap-3">
              <span className="flex items-center justify-center w-6 h-6 rounded bg-emerald-500/20 text-emerald-400 text-xs font-mono border border-emerald-500/30">5</span>
              Výpočet nákladov na Vlastnú serverovňu (On-Premise)
            </div>
            <span className="text-slate-500 group-open:rotate-180 transition-transform">▼</span>
          </summary>
          <div className="px-6 pb-6 pt-2 border-t border-white/5 space-y-4">
            <div className="bg-slate-900 p-4 rounded-lg font-mono text-xs text-slate-300 space-y-2 border border-slate-800">
              <p className="text-slate-500">// CAPEX náklady sa rozpočítavajú (amortizujú) na počet mesiacov odpisovania.</p>
              <p className="text-slate-500">// Energia a chladenie bežia 24/7 bez ohľadu na vyťaženie.</p>
              <br/>
              <p><span className="text-pink-400">HW_Capex</span> = Total_Nodes × Hardware_Cost_Per_Node</p>
              <p><span className="text-pink-400">Monthly_HW_Amortization</span> = HW_Capex / Amortization_Months</p>
              <p><span className="text-pink-400">Monthly_Power</span> = Total_Nodes × Node_kW × (24h × 30.4 dní) × Price_per_kWh</p>
              <p><span className="text-emerald-400 font-bold">OnPremise_Total</span> = Monthly_HW_Amortization + Monthly_Power + MLOps_Admin</p>
            </div>
          </div>
        </details>
      </div>
    </div>
  );
}
