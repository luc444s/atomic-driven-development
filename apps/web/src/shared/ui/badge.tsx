import { HTMLAttributes } from "react";

import { cn } from "./cn";

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-slate-700 bg-slate-900 px-2.5 py-1 text-xs font-medium text-slate-200",
        className
      )}
      {...props}
    />
  );
}
