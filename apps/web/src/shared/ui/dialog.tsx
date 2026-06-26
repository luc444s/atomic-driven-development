import { ReactNode } from "react";

import { cn } from "./cn";

type DialogProps = {
  open: boolean;
  title: string;
  description?: string;
  children: ReactNode;
  actions?: ReactNode;
  onClose: () => void;
};

export function Dialog({
  open,
  title,
  description,
  children,
  actions,
  onClose,
}: DialogProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4">
      <div className="w-full max-w-2xl rounded-xl border border-slate-800 bg-slate-950 shadow-xl">
        <div className="flex items-start justify-between gap-4 border-b border-slate-800 p-5">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-white">{title}</h2>
            {description ? <p className="text-sm text-slate-400">{description}</p> : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className={cn(
              "rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-300",
              "hover:bg-slate-900 hover:text-white"
            )}
          >
            Cerrar
          </button>
        </div>
        <div className="p-5">{children}</div>
        {actions ? <div className="border-t border-slate-800 p-5">{actions}</div> : null}
      </div>
    </div>
  );
}
