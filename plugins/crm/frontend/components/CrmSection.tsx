import { ReactNode } from "react";

type CrmSectionProps = {
  title: string;
  description: string;
  actions?: ReactNode;
  children: ReactNode;
};

export function CrmSection({ title, description, actions, children }: CrmSectionProps) {
  return (
    <section className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">CRM</p>
          <h1 className="text-xl font-semibold text-white">{title}</h1>
          <p className="max-w-2xl text-sm text-slate-400">{description}</p>
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}
