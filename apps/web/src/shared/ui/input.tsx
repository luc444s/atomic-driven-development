import { InputHTMLAttributes, forwardRef } from "react";

import { cn } from "./cn";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...props }, ref) {
    return (
      <input
        ref={ref}
        className={cn(
          "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-50 outline-none transition placeholder:text-slate-500 focus:border-cyan-500",
          className
        )}
        {...props}
      />
    );
  }
);
