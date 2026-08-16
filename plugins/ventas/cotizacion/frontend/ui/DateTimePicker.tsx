import { useState } from "react";
import { Input } from "@systutor/shell/ui/input";
import { formatDate, resolveDate } from "../../../_shared/frontend/utils/date-resolver";

export interface DateTimePickerProps {
  dateValue: string;
  timeValue: string;
  onDateChange: (date: string) => void;
  onTimeChange: (time: string) => void;
}

export function DateTimePicker({
  dateValue,
  timeValue,
  onDateChange,
  onTimeChange,
}: DateTimePickerProps) {
  const [showDateShortcuts, setShowDateShortcuts] = useState(false);

  const today = formatDate(new Date());
  const tomorrow = formatDate(resolveDate("mañana") ?? new Date());

  return (
    <label className="block space-y-2 text-sm text-foreground">
      <span>Fecha y hora de entrega</span>
      <div className="flex gap-2">
        <div className="flex-1">
          <Input
            type="date"
            value={dateValue}
            onChange={(e) => onDateChange(e.target.value)}
            min={today}
            className="text-sm h-9"
            onFocus={() => setShowDateShortcuts(true)}
            onBlur={() => setTimeout(() => setShowDateShortcuts(false), 200)}
          />
          {showDateShortcuts && (
            <div className="flex gap-1 mt-1">
              <button
                type="button"
                onClick={() => onDateChange(today)}
                className="text-xs px-2 py-0.5 rounded border border-border bg-surface hover:bg-accent text-muted-foreground hover:text-foreground transition"
              >
                Hoy
              </button>
              <button
                type="button"
                onClick={() => onDateChange(tomorrow)}
                className="text-xs px-2 py-0.5 rounded border border-border bg-surface hover:bg-accent text-muted-foreground hover:text-foreground transition"
              >
                Mañana
              </button>
            </div>
          )}
        </div>
        <div className="w-28 shrink-0">
          <Input
            type="time"
            value={timeValue}
            onChange={(e) => onTimeChange(e.target.value)}
            className="text-sm h-9"
          />
        </div>
      </div>
    </label>
  );
}
