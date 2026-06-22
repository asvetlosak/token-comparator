import React from 'react';

interface RiskSectionProps {
  includeAdminSalary: boolean;
}

export default function RiskSection({ includeAdminSalary }: RiskSectionProps) {
  return (
    <section className="space-y-6">
      <div className="glass-card p-6 border-l-4 border-amber-500">
        <h2 className="text-xl font-bold text-white mb-2">Riziká a Skryté náklady (Cloud & On-Premise)</h2>
        <p className="text-sm text-slate-400">
          Kalkulačka poskytuje ideálny teoretický scenár. V reálnom svete obnáša vlastná prevádzka AI modelov
          ďalšie nezanedbateľné náklady a inžinierske výzvy v porovnaní s API.
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-3">
            <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-500/20 text-amber-400">Vysoké</span>
            <h4 className="font-semibold text-white">Nízka utilizácia (On-Premise vs Cloud)</h4>
          </div>
          <p className="text-sm text-slate-400">
            Kalkulačka pre Cloud Server uvažuje "Scale-to-Zero" – platíte len za pracovné hodiny. 
            Pri vlastnej serverovni (On-Premise) ale HW amortizácia a energia bežia 24/7. Mimo pracovnej špičky bude HW nevyužitý, čím klesá jeho reálna efektivita, pokiaľ nemáte vyťažené nočné batch-processing úlohy.
          </p>
        </div>

        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-3">
            <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-500/20 text-amber-400">Vysoké</span>
            <h4 className="font-semibold text-white">Hardware zlyhania a SLA</h4>
          </div>
          <p className="text-sm text-slate-400">
            Pri výpadku GPU uzla vo vlastnej réžii potrebujete redundanciu (n+1), čo ďalej zvyšuje CAPEX. Cloud API provideri
            túto vrstvu riešia za vás a garantujú SLA transparentne.
          </p>
        </div>

        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-3">
            <span className="px-2 py-0.5 rounded text-xs font-bold bg-yellow-500/20 text-yellow-400">Stredné</span>
            <h4 className="font-semibold text-white">Rýchle zastarávanie HW</h4>
          </div>
          <p className="text-sm text-slate-400">
            Modely sa menia každý mesiac. Nákup HW (On-Premise) alebo dlhodobá rezervácia instancií pre zľavu
            vás uzamkne na hardvéri, ktorý môže byť pre budúce architektúry neoptimálny (napr. nedostatok pamäte pre obrovský KV Cache).
          </p>
        </div>
        
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-3">
            <span className="px-2 py-0.5 rounded text-xs font-bold bg-yellow-500/20 text-yellow-400">Stredné</span>
            <h4 className="font-semibold text-white">Skryté sieťové poplatky</h4>
          </div>
          <p className="text-sm text-slate-400">
            Pri Cloud Serveroch si dajte pozor na poplatky za "Egress" (dáta tečúce von z cloudu). Pri obrovskom objeme tokenov môžu sieťové prenosy vytvoriť nečakanú položku vo faktúre. Naopak, API to má väčšinou v cene tokenu.
          </p>
        </div>
      </div>
    </section>
  );
}
