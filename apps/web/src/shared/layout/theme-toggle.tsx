import { useThemeStore } from "../../features/theme/store";

const THEME_LABELS: Record<string, string> = {
  dark: "Oscuro",
  light: "Claro",
  retro: "Retro (SAP)",
};

export function ThemeToggle() {
  const theme = useThemeStore((s) => s.theme);
  const setTheme = useThemeStore((s) => s.setTheme);

  return (
    <label className="flex items-center gap-2 text-xs text-muted-foreground">
      <span>Tema</span>
      <select
        value={theme}
        onChange={(e) => setTheme(e.target.value as typeof theme)}
        className="rounded-md border border-border bg-card px-2 py-1 text-xs text-foreground"
      >
        {Object.entries(THEME_LABELS).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
    </label>
  );
}
