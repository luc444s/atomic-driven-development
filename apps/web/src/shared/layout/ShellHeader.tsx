type ShellHeaderProps = {
  tenantName: string | null;
  branchName: string | null;
  userName: string | null;
  userEmail: string | null;
};

export function ShellHeader({
  tenantName,
  branchName,
  userName,
  userEmail,
}: ShellHeaderProps) {
  return (
    <div className="space-y-1">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Core shell</p>
      <h1 className="text-lg font-semibold text-white">Operacion base del sistema</h1>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
        <span>
          Tenant: <span className="text-slate-200">{tenantName ?? "Sin tenant"}</span>
        </span>
        <span>
          Branch: <span className="text-slate-200">{branchName ?? "Sin branch"}</span>
        </span>
        <span>
          User: <span className="text-slate-200">{userName ?? userEmail ?? "Sesion activa"}</span>
        </span>
      </div>
    </div>
  );
}
