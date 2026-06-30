type SettingsPageProps = {
  title: string;
  description: string;
};

export function SettingsPage({ title, description }: SettingsPageProps) {
  return (
    <section className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>

      <div className="rounded-xl border border-border bg-card p-5 text-sm text-muted-foreground">
        Este milestone solo prepara el shell tenant-specific del core. El CRUD real se implementa en
        una iteracion posterior.
      </div>
    </section>
  );
}
