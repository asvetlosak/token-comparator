import { DEFAULTS } from '../data/constants';

interface InputPanelProps {
  totalMonthlyTokensM: number;
  setTotalMonthlyTokensM: (v: number) => void;
  inputRatio: number;
  setInputRatio: (v: number) => void;
  workDays: number;
  setWorkDays: (v: number) => void;
  hoursPerDay: number;
  setHoursPerDay: (v: number) => void;
  peakMultiplier: number;
  setPeakMultiplier: (v: number) => void;
  includeAdminSalary: boolean;
  setIncludeAdminSalary: (v: boolean) => void;
  adminSalary: number;
  setAdminSalary: (v: number) => void;
  amortizationMonths: number;
  setAmortizationMonths: (v: number) => void;
  powerCostPerNodePerMonth: number;
  setPowerCostPerNodePerMonth: (v: number) => void;
}

export default function InputPanel({
  totalMonthlyTokensM,
  setTotalMonthlyTokensM,
  inputRatio,
  setInputRatio,
  workDays,
  setWorkDays,
  hoursPerDay,
  setHoursPerDay,
  peakMultiplier,
  setPeakMultiplier,
  includeAdminSalary,
  setIncludeAdminSalary,
  adminSalary,
  setAdminSalary,
  amortizationMonths,
  setAmortizationMonths,
  powerCostPerNodePerMonth,
  setPowerCostPerNodePerMonth,
}: InputPanelProps) {
  return (
    <div className="space-y-3">
      {/* Sekcia 1: Tím a Spotreba */}
      <div className="bg-slate-900/50 p-4 rounded-xl border border-white/5 space-y-3">
        <h3 className="section-label">👥 Tím & Spotreba</h3>
        
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-slate-300">
            <label>Celkový počet tokenov (Milióny/mes.)</label>
            <input 
              type="number" 
              value={totalMonthlyTokensM} 
              onChange={(e) => setTotalMonthlyTokensM(Number(e.target.value))}
              className="w-24 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-right font-mono text-indigo-400"
            />
          </div>
          <input 
            type="range" 
            min="1000" max="100000" step="1000"
            value={totalMonthlyTokensM} 
            onChange={(e) => setTotalMonthlyTokensM(Number(e.target.value))}
            className="w-full accent-indigo-500"
          />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm text-slate-300">
            <label>Peak multiplier</label>
            <input 
              type="number" 
              step="0.1"
              value={peakMultiplier} 
              onChange={(e) => setPeakMultiplier(Number(e.target.value))}
              className="w-20 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-right font-mono text-indigo-400"
            />
          </div>
          <input 
            type="range" 
            min="1" max="10" step="0.1"
            value={peakMultiplier} 
            onChange={(e) => setPeakMultiplier(Number(e.target.value))}
            className="w-full accent-indigo-500"
          />
        </div>


        <div className="space-y-2">
          <div className="flex justify-between text-sm text-slate-300">
            <label>Pomer Input/Output</label>
            <span className="font-mono text-indigo-400">{(inputRatio * 100).toFixed(0)}% input / {((1 - inputRatio) * 100).toFixed(0)}% output</span>
          </div>
          <input 
            type="range" 
            min="0" max="100" 
            value={inputRatio * 100} 
            onChange={(e) => setInputRatio(Number(e.target.value) / 100)}
            className="w-full accent-indigo-500"
          />
        </div>
      </div>

      {/* Sekcia 2: Pracovné hodiny */}
      <div className="bg-slate-900/50 p-4 rounded-xl border border-white/5 space-y-3">
        <h3 className="section-label">⏰ Pracovné hodiny</h3>
        
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-slate-300">
            <label>Pracovné dni v mesiaci</label>
            <input 
              type="number" 
              value={workDays} 
              onChange={(e) => setWorkDays(Number(e.target.value))}
              className="w-20 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-right font-mono text-indigo-400"
            />
          </div>
          <input 
            type="range" 
            min="1" max="31" 
            value={workDays} 
            onChange={(e) => setWorkDays(Number(e.target.value))}
            className="w-full accent-indigo-500"
          />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm text-slate-300">
            <label>Hodiny denne</label>
            <input 
              type="number" 
              value={hoursPerDay} 
              onChange={(e) => setHoursPerDay(Number(e.target.value))}
              className="w-20 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-right font-mono text-indigo-400"
            />
          </div>
          <input 
            type="range" 
            min="1" max="24" 
            value={hoursPerDay} 
            onChange={(e) => setHoursPerDay(Number(e.target.value))}
            className="w-full accent-indigo-500"
          />
        </div>


      </div>

      {/* Sekcia 3: Dodatočné náklady */}
      <div className="bg-slate-900/50 p-4 rounded-xl border border-white/5 space-y-3">
        <h3 className="section-label">💰 Dodatočné náklady</h3>
        
        <div className="flex items-center justify-between">
          <label className="text-sm text-slate-300 cursor-pointer" onClick={() => setIncludeAdminSalary(!includeAdminSalary)}>
            Započítať plat MLOps inžiniera
          </label>
          <div 
            className={`toggle-switch ${includeAdminSalary ? 'active' : ''}`}
            onClick={() => setIncludeAdminSalary(!includeAdminSalary)}
          />
        </div>

        {includeAdminSalary && (
          <div className="space-y-2 pt-2 border-t border-slate-700/50">
            <div className="flex justify-between items-center text-sm text-slate-300">
              <label>Mesačný plat admina (USD)</label>
              <input 
                type="number" 
                value={adminSalary} 
                onChange={(e) => setAdminSalary(Number(e.target.value))}
                className="w-24 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-right font-mono text-indigo-400"
              />
            </div>
          </div>
        )}
      </div>

      {/* Sekcia 4: On-Premise (Vlastná serverovňa) */}
      <div className="bg-slate-900/50 p-4 rounded-xl border border-white/5 space-y-3">
        <h3 className="section-label">🏢 On-Premise (Nákup HW)</h3>
        
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-slate-300">
            <label>Doba odpisovania HW (mesiace)</label>
            <input 
              type="number" 
              value={amortizationMonths} 
              onChange={(e) => setAmortizationMonths(Number(e.target.value))}
              className="w-20 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-right font-mono text-purple-400"
            />
          </div>
          <input 
            type="range" 
            min="12" max="60" 
            value={amortizationMonths} 
            onChange={(e) => setAmortizationMonths(Number(e.target.value))}
            className="w-full accent-purple-500"
          />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm text-slate-300">
            <label>Elektrina a Chladenie (na uzol/mesačne)</label>
            <div className="relative w-28">
              <span className="absolute left-2 top-1 text-slate-400">€</span>
              <input 
                type="number" 
                value={powerCostPerNodePerMonth} 
                onChange={(e) => setPowerCostPerNodePerMonth(Number(e.target.value))}
                className="w-full bg-slate-800 border border-slate-700 rounded pl-6 pr-2 py-1 text-right font-mono text-purple-400"
              />
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
