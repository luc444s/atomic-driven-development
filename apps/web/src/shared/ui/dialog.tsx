import { ReactNode } from "react";
import { cn } from "./cn";

type DialogProps = {
  open: boolean;
  title: string;
  description?: string;
  children: ReactNode;
  actions?: ReactNode;
  onClose: () => void;
  maxWidthClassName?: string;
  maxHeightClassName?: string;
  zIndexClassName?: string;
};

export function Dialog({
  open,
  title,
  description,
  children,
  actions,
  onClose,
  maxWidthClassName = "max-w-2xl",
  maxHeightClassName = "max-h-[85vh]",
  zIndexClassName = "z-[1000]",
}: DialogProps) {
  if (!open) return null;

  return (
    <div
      className={cn("fixed inset-0 flex items-center justify-center bg-background/80 p-4", zIndexClassName)}
      onClick={onClose}
    >
      <div
        className={cn(
          "flex w-full flex-col overflow-hidden rounded-xl border border-border bg-card shadow-xl",
          maxHeightClassName,
          maxWidthClassName
        )}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-border p-5">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-card-foreground">{title}</h2>
            {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className={cn(
              "rounded-md border border-border px-3 py-1.5 text-sm text-muted-foreground",
              "hover:bg-accent hover:text-accent-foreground transition"
            )}
          >
            Cerrar
          </button>
        </div>
        <div className="overflow-y-auto p-5">{children}</div>
        {actions ? <div className="border-t border-border p-5">{actions}</div> : null}
      </div>
    </div>
  );
}
