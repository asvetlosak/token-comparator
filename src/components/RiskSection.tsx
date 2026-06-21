import React from 'react';

interface RiskSectionProps {
  includeAdminSalary: boolean;
}

export default function RiskSection({ includeAdminSalary }: RiskSectionProps) {
  return (
    <section className="space-y-6">
      <div className="glass-card p-6 border-l-4 border-amber-500">
        <h2 className="text-xl font-bold text-white mb-2">Riziká a Skryté náklady (Cloud Server)</h2>
        <p className="text-sm text-slate-400">
          Kalkulačka poskytuje ideálny teoretický scenár. V reálnom svete obnáša prevádzka na cloud serveroch
          ďalšie nezanedbateľné náklady a inžinierske výzvy.
        </p>
      </div>

      {!includeAdminSalary && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-5 flex gap-4">
          <div className="text-2xl">⚠️</div>
          <div>
            <h3 className="font-bold text-red-400 mb-1">Kritické varovanie: Chýbajúci personál</h3>
            <p className="text-sm text-slate-300">
              Vo výpočte aktuálne nezohľadňujete plat MLOps inžiniera. Správa GPU klastra pre produkciu
              nie je jednorazová záležitosť. Vyžaduje experta na vLLM, load balancing, Kubernetes a monitoring.
              Zvážte zapnutie tejto položky v nastaveniach.
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-3">
            <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-500/20 text-amber-400">Vysoké</span>
            <h4 className="font-semibold text-white">Nízka utilizácia</h4>
          </div>
          <p className="text-sm text-slate-400">
            Tento výpočet predpokladá využitie iba počas pracovnej doby (napr. 10h/deň).
            GPU server beží a stojí peniaze 24/7. Mimo špičky bude jeho utilizácia takmer nulová,
            pokiaľ nemáte nočné batch-processing úlohy.
          </p>
        </div>

        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-3">
            <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-500/20 text-amber-400">Vysoké</span>
            <h4 className="font-semibold text-white">Hardware zlyhania</h4>
          </div>
          <p className="text-sm text-slate-400">
            Pri výpadku GPU uzla potrebujete redundanciu. Cloud API provideri
            garantujú SLA a riešia výpadky transparentne.
          </p>
        </div>

        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-3">
            <span className="px-2 py-0.5 rounded text-xs font-bold bg-yellow-500/20 text-yellow-400">Stredné</span>
            <h4 className="font-semibold text-white">Rýchle zastarávanie</h4>
          </div>
          <p className="text-sm text-slate-400">
            Modely sa menia každý mesiac. Rezervácia ročných instancií pre zľavu
            (často až 50%) vás uzamkne na hardvéri, ktorý môže byť pre budúce architektúry neoptimálny.
          </p>
        </div>
      </div>
    </section>
  );
}
