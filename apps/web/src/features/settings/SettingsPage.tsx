type SettingsPageProps = {
  title: string;
  description: string;
};

export function SettingsPage({ title, description }: SettingsPageProps) {
  return (
    <section className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-white">{title}</h1>
        <p className="text-sm text-slate-400">{description}</p>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-5 text-sm text-slate-300">
        Este milestone solo prepara el shell tenant-specific del core. El CRUD real se implementa en
        una iteracion posterior.
      </div>
    </section>
  );
}
