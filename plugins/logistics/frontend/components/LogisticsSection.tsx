import { ReactNode } from "react";

import { LogisticsNav } from "./LogisticsNav";

type LogisticsSectionProps = {
  eyebrow?: string;
  title: string;
  description: string;
  actions?: ReactNode;
  children: ReactNode;
};

export function LogisticsSection({
  eyebrow = "Logistics",
  title,
  description,
  actions,
  children,
}: LogisticsSectionProps) {
  return (
    <section className="space-y-6">
      <div className="space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">{eyebrow}</p>
            <h1 className="text-xl font-semibold text-white">{title}</h1>
            <p className="max-w-2xl text-sm text-slate-400">{description}</p>
          </div>
          {actions}
        </div>
        <LogisticsNav />
      </div>
      {children}
    </section>
  );
}
