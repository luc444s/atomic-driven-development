import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { Check, ChevronsUpDown } from "lucide-react";

import { cn } from "./cn";
import { Input } from "./input";

export type ComboboxOption = {
  value: string;
  label: string;
  keywords?: string[];
};

type ComboboxProps = {
  value: string;
  onChange: (value: string) => void;
  options: ComboboxOption[];
  placeholder?: string;
  searchPlaceholder?: string;
  emptyMessage?: string;
  className?: string;
  required?: boolean;
  disabled?: boolean;
};

function normalize(value: string) {
  return value
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .trim();
}

export function Combobox({
  value,
  onChange,
  options,
  placeholder,
  searchPlaceholder,
  emptyMessage = "Sin opciones.",
  className,
  required,
  disabled,
}: ComboboxProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const selected = options.find((option) => option.value === value) ?? null;

  const filteredOptions = useMemo(() => {
    const normalizedQuery = normalize(query);
    if (!normalizedQuery) {
      return options;
    }
    return options.filter((option) => {
      const haystack = [option.label, ...(option.keywords ?? [])]
        .map(normalize)
        .join(" ");
      return haystack.includes(normalizedQuery);
    });
  }, [options, query]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!open) {
      setQuery("");
      return;
    }
    const selectedIndex = filteredOptions.findIndex((option) => option.value === value);
    setHighlightedIndex(selectedIndex >= 0 ? selectedIndex : 0);
    const timer = window.setTimeout(() => inputRef.current?.focus(), 0);
    return () => window.clearTimeout(timer);
  }, [open, filteredOptions, value]);

  useEffect(() => {
    if (highlightedIndex >= filteredOptions.length) {
      setHighlightedIndex(filteredOptions.length > 0 ? filteredOptions.length - 1 : 0);
    }
  }, [filteredOptions, highlightedIndex]);

  function selectOption(option: ComboboxOption) {
    onChange(option.value);
    setOpen(false);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement | HTMLInputElement>) {
    if (!open && (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ")) {
      event.preventDefault();
      if (!disabled) {
        setOpen(true);
      }
      return;
    }

    if (!open) {
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      setOpen(false);
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlightedIndex((current) => {
        if (filteredOptions.length === 0) return 0;
        return current >= filteredOptions.length - 1 ? 0 : current + 1;
      });
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlightedIndex((current) => {
        if (filteredOptions.length === 0) return 0;
        return current <= 0 ? filteredOptions.length - 1 : current - 1;
      });
      return;
    }

    if (event.key === "Enter" && filteredOptions[highlightedIndex]) {
      event.preventDefault();
      selectOption(filteredOptions[highlightedIndex]);
    }
  }

  return (
    <div ref={ref} className="relative" onKeyDown={handleKeyDown}>
      <button
        type="button"
        disabled={disabled}
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-required={required}
        onClick={() => {
          if (!disabled) {
            setOpen((current) => !current);
          }
        }}
        className={cn(
          "flex w-full items-center justify-between gap-2 rounded-md border border-input bg-surface px-3 py-2 text-sm text-foreground transition hover:border-ring disabled:cursor-not-allowed disabled:opacity-60",
          !selected && placeholder && "text-muted-foreground",
          open && "border-ring ring-1 ring-ring",
          className
        )}
      >
        <span className="truncate text-left">{selected?.label ?? placeholder ?? "Seleccionar"}</span>
        <ChevronsUpDown className="h-4 w-4 shrink-0 text-muted-foreground" />
      </button>

      {open ? (
        <div className="absolute left-0 right-0 top-full z-50 mt-1 rounded-md border border-border bg-popover shadow-lg">
          <div className="border-b border-border p-2">
            <Input
              ref={inputRef}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={searchPlaceholder ?? "Buscar..."}
            />
          </div>

          <div className="max-h-60 overflow-auto py-1" role="listbox">
            {filteredOptions.length > 0 ? (
              filteredOptions.map((option, index) => {
                const isSelected = option.value === value;
                const isHighlighted = index === highlightedIndex;

                return (
                  <button
                    key={option.value}
                    type="button"
                    role="option"
                    aria-selected={isSelected}
                    onMouseEnter={() => setHighlightedIndex(index)}
                    onClick={() => selectOption(option)}
                    className={cn(
                      "flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition",
                      isHighlighted
                        ? "bg-accent text-accent-foreground"
                        : "text-popover-foreground hover:bg-accent hover:text-accent-foreground"
                    )}
                  >
                    <Check className={cn("h-4 w-4 shrink-0", isSelected ? "opacity-100" : "opacity-0")} />
                    <span className="truncate">{option.label}</span>
                  </button>
                );
              })
            ) : (
              <p className="px-3 py-2 text-sm text-muted-foreground">{emptyMessage}</p>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
