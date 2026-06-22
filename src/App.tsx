import { useState, useMemo } from 'react';
import InputPanel from './components/InputPanel';
import MatrixResults from './components/MatrixResults';
import CalculationDetails from './components/CalculationDetails';
import RiskSection from './components/RiskSection';
import { calculateMatrix, type MatrixInputs } from './utils/calculations';
import { DEFAULTS } from './data/constants';
import { LayoutGrid, Cpu, TrendingUp, HelpCircle, AlertTriangle } from 'lucide-react';

export default function App() {
  const [totalMonthlyTokensM, setTotalMonthlyTokensM] = useState(DEFAULTS.totalMonthlyTokensM);
  const [inputRatio, setInputRatio] = useState(DEFAULTS.inputRatio);
  const [workDays, setWorkDays] = useState(DEFAULTS.workDaysPerMonth);
  const [hoursPerDay, setHoursPerDay] = useState(DEFAULTS.hoursPerDay);
  const [peakMultiplier, setPeakMultiplier] = useState(DEFAULTS.peakMultiplier);
  const [includeAdminSalary, setIncludeAdminSalary] = useState(DEFAULTS.includeAdminSalary);
  const [adminSalaryPerMonth, setAdminSalaryPerMonth] = useState(DEFAULTS.adminSalaryPerMonth);
  const [amortizationMonths, setAmortizationMonths] = useState(DEFAULTS.amortizationMonths);
  const [powerCostPerNodePerMonth, setPowerCostPerNodePerMonth] = useState(DEFAULTS.powerCostPerNodePerMonth);

  const [activeTab, setActiveTab] = useState<'matrix' | 'methodology' | 'risks'>('matrix');

  const matrixInputs: MatrixInputs = useMemo(() => ({
    totalMonthlyTokensM,
    inputRatio,
    workDaysPerMonth: workDays,
    hoursPerDay,
    peakMultiplier,
    includeAdminSalary,
    adminSalaryPerMonth,
    amortizationMonths,
    powerCostPerNodePerMonth,
    avgContextLength: DEFAULTS.avgContextLength,
    quantization: DEFAULTS.quantization,
  }), [totalMonthlyTokensM, inputRatio, workDays, hoursPerDay, peakMultiplier, includeAdminSalary, adminSalaryPerMonth, amortizationMonths, powerCostPerNodePerMonth]);

  const { workload, matrix } = useMemo(() => calculateMatrix(matrixInputs), [matrixInputs]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 selection:bg-indigo-500/30">
      <div className="max-w-[1600px] mx-auto px-4 py-8">
        <header className="mb-8">
          <h1 className="text-3xl font-extrabold flex items-center gap-3">
            <span>🇪🇺</span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-cyan-400">EU AI Infrastructure TCO Comparator</span>
            <span className="text-2xl">🤖 🖥️</span>
          </h1>
          <p className="text-slate-400 mt-2 text-sm max-w-3xl">
            Interaktívna maticová kalkulačka na porovnanie celkových nákladov (TCO) medzi vlastnou serverovňou (On-Premise), prenájmom Cloud Server klastra a využívaním managed API pre top Open-Weight modely v Európe.
          </p>
        </header>

        <div className="flex flex-col xl:flex-row gap-8 items-start">
          <aside className="w-full xl:w-80 shrink-0 sticky top-4 xl:top-8 max-h-[calc(100vh-2rem)] overflow-y-auto pr-1">
            <InputPanel
              totalMonthlyTokensM={totalMonthlyTokensM}
              setTotalMonthlyTokensM={setTotalMonthlyTokensM}
              inputRatio={inputRatio}
              setInputRatio={setInputRatio}
              workDays={workDays}
              setWorkDays={setWorkDays}
              hoursPerDay={hoursPerDay}
              setHoursPerDay={setHoursPerDay}
              peakMultiplier={peakMultiplier}
              setPeakMultiplier={setPeakMultiplier}
              includeAdminSalary={includeAdminSalary}
              setIncludeAdminSalary={setIncludeAdminSalary}
              adminSalary={adminSalaryPerMonth}
              setAdminSalary={setAdminSalaryPerMonth}
              amortizationMonths={amortizationMonths}
              setAmortizationMonths={setAmortizationMonths}
              powerCostPerNodePerMonth={powerCostPerNodePerMonth}
              setPowerCostPerNodePerMonth={setPowerCostPerNodePerMonth}
            />
          </aside>

          <main className="flex-1 min-w-0">
            <div className="glass-card mb-8 p-2 flex gap-2 overflow-x-auto hide-scrollbar">
              <button
                className={`flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-lg text-sm font-semibold transition-all ${
                  activeTab === 'matrix' ? 'bg-indigo-500/20 text-indigo-300' : 'text-slate-400 hover:bg-white/5'
                }`}
                onClick={() => setActiveTab('matrix')}
              >
                <LayoutGrid className="w-4 h-4" /> Porovnávacia matica
              </button>
              <button
                className={`flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-lg text-sm font-semibold transition-all ${
                  activeTab === 'methodology' ? 'bg-purple-500/20 text-purple-300' : 'text-slate-400 hover:bg-white/5'
                }`}
                onClick={() => setActiveTab('methodology')}
              >
                <HelpCircle className="w-4 h-4" /> Metodika a Zdroje
              </button>
              <button
                className={`flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-lg text-sm font-semibold transition-all ${
                  activeTab === 'risks' ? 'bg-amber-500/20 text-amber-300' : 'text-slate-400 hover:bg-white/5'
                }`}
                onClick={() => setActiveTab('risks')}
              >
                <AlertTriangle className="w-4 h-4" /> Riziká a Skryté náklady
              </button>
            </div>

            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              {activeTab === 'matrix' && (
                <MatrixResults matrix={matrix} workload={workload} inputs={matrixInputs} />
              )}

              {activeTab === 'methodology' && (
                <CalculationDetails />
              )}

              {activeTab === 'risks' && (
                <RiskSection includeAdminSalary={includeAdminSalary} />
              )}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
