export type ThemeName = "light" | "dark" | "retro";

export type ThemeTokens = {
  // ----- Palette (26 vars) -----
  colorScheme: string;
  background: string;
  foreground: string;
  card: string;
  cardForeground: string;
  popover: string;
  popoverForeground: string;
  primary: string;
  primaryForeground: string;
  secondary: string;
  secondaryForeground: string;
  muted: string;
  mutedForeground: string;
  accent: string;
  accentForeground: string;
  destructive: string;
  destructiveForeground: string;
  border: string;
  input: string;
  ring: string;
  sidebar: string;
  sidebarForeground: string;
  sidebarMuted: string;
  surface: string;
  surfaceAlt: string;
  radius: string;
  cardShadow: string;

  // ----- Typography -----
  fontFamily: string; // "" = no override (app default)
  fontSmoothing: "antialiased" | "none" | "inherit";
  baseFontSize: string; // "" = no override
  moduleTitleTransform: "uppercase" | "none";
  moduleTitleSize: string; // "" = no override
  moduleTitleWeight: string; // "" = no override
  moduleTitlePadding: string; // "" = no override

  // ----- Sidebar links -----
  sidebarItemPadding: string; // "" = no override
  sidebarIndent: string; // "" = no override (border-left width)
  sidebarLinkSize: string; // "" = no override
  sidebarLinkWeight: string; // "" = no override

  // ----- Spacing / separations ("" = no override, Tailwind default) -----
  spaceY: string;
  spaceX: string;
  cardPadding: string;
  sectionPadding: string;

  // ----- Radius / shadow -----
  enforceRadius: "full" | "none";
  enforceShadow: "full" | "none";

  // ----- Buttons -----
  buttonRadius: string; // "" = no override
  buttonPadding: string; // "" = no override

  // ----- Tables -----
  tableFontSize: string; // "" = no override
  tableCellPadding: string; // "" = no override
  tableBorder: "bordered" | "none";
  tableBorderCollapse: "collapse" | "separate";
  tableHeaderBg: "primary" | "themed" | "none";
  tableZebra: "surface-alt" | "none";

  // ----- Header bar -----
  headerStyle: "primary" | "themed";

  // ----- Sidebar active item -----
  sidebarActiveStyle: "primary" | "themed";
};

const NO_OVERRIDE = {
  fontFamily: "",
  fontSmoothing: "inherit" as const,
  baseFontSize: "",
  moduleTitleTransform: "none" as const,
  moduleTitleSize: "",
  moduleTitleWeight: "",
  moduleTitlePadding: "",
  sidebarItemPadding: "",
  sidebarIndent: "",
  sidebarLinkSize: "",
  sidebarLinkWeight: "",
  spaceY: "",
  spaceX: "",
  cardPadding: "",
  sectionPadding: "",
  enforceRadius: "full" as const,
  enforceShadow: "full" as const,
  buttonRadius: "",
  buttonPadding: "",
  tableFontSize: "",
  tableCellPadding: "",
  tableBorder: "none" as const,
  tableBorderCollapse: "separate" as const,
  tableHeaderBg: "none" as const,
  tableZebra: "none" as const,
  headerStyle: "themed" as const,
  sidebarActiveStyle: "themed" as const,
};

export const themes: Record<ThemeName, ThemeTokens> = {
  light: {
    colorScheme: "light",
    background: "210 40% 95%",
    foreground: "222 47% 11%",
    card: "0 0% 99%",
    cardForeground: "222 47% 11%",
    popover: "0 0% 99%",
    popoverForeground: "222 47% 11%",
    primary: "187 85% 43%",
    primaryForeground: "0 0% 100%",
    secondary: "210 40% 96%",
    secondaryForeground: "222 47% 11%",
    muted: "210 40% 96%",
    mutedForeground: "215 20% 45%",
    accent: "210 40% 96%",
    accentForeground: "222 47% 11%",
    destructive: "0 60% 50%",
    destructiveForeground: "0 0% 100%",
    border: "0 0% 75%",
    input: "0 0% 50%",
    ring: "187 85% 43%",
    sidebar: "210 40% 99%",
    sidebarForeground: "222 47% 11%",
    sidebarMuted: "215 20% 65%",
    surface: "0 0% 99%",
    surfaceAlt: "210 40% 96%",
    radius: "0.5rem",
    cardShadow: "0 4px 12px -2px rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.05)",
    ...NO_OVERRIDE,
  },
  dark: {
    colorScheme: "dark",
    background: "0 0% 4%",
    foreground: "0 0% 90%",
    card: "0 0% 7%",
    cardForeground: "0 0% 90%",
    popover: "0 0% 7%",
    popoverForeground: "0 0% 90%",
    primary: "187 85% 53%",
    primaryForeground: "0 0% 4%",
    secondary: "0 0% 12%",
    secondaryForeground: "0 0% 90%",
    muted: "0 0% 12%",
    mutedForeground: "0 0% 55%",
    accent: "0 0% 14%",
    accentForeground: "0 0% 90%",
    destructive: "0 63% 31%",
    destructiveForeground: "0 0% 90%",
    border: "0 0% 16%",
    input: "0 0% 22%",
    ring: "187 85% 53%",
    sidebar: "0 0% 5%",
    sidebarForeground: "0 0% 90%",
    sidebarMuted: "0 0% 55%",
    surface: "0 0% 7%",
    surfaceAlt: "0 0% 12%",
    radius: "0.5rem",
    cardShadow: "0 0 0 0 transparent",
    ...NO_OVERRIDE,
  },
  retro: {
    colorScheme: "light",
    background: "0 0% 89%",
    foreground: "0 0% 0%",
    card: "0 0% 100%",
    cardForeground: "0 0% 0%",
    popover: "0 0% 100%",
    popoverForeground: "0 0% 0%",
    primary: "209 79% 28%",
    primaryForeground: "0 0% 100%",
    secondary: "0 0% 92%",
    secondaryForeground: "0 0% 0%",
    muted: "0 0% 94%",
    mutedForeground: "0 0% 25%",
    accent: "207 56% 92%",
    accentForeground: "0 0% 0%",
    destructive: "0 70% 35%",
    destructiveForeground: "0 0% 100%",
    border: "0 0% 65%",
    input: "0 0% 50%",
    ring: "209 79% 28%",
    sidebar: "0 0% 85%",
    sidebarForeground: "0 0% 0%",
    sidebarMuted: "0 0% 25%",
    surface: "0 0% 100%",
    surfaceAlt: "0 0% 94%",
    radius: "0",
    cardShadow: "0 0 0 0 transparent",
    fontFamily: '"PT Sans", Verdana, Tahoma, Geneva, sans-serif',
    fontSmoothing: "none",
    baseFontSize: "14px",
    moduleTitleTransform: "uppercase",
    moduleTitleSize: "11px",
    moduleTitleWeight: "700",
    moduleTitlePadding: "3px 6px",
    sidebarItemPadding: "1px 6px 1px 28px",
    sidebarIndent: "2px",
    sidebarLinkSize: "11px",
    sidebarLinkWeight: "400",
    spaceY: "2px",
    spaceX: "2px",
    cardPadding: "6px",
    sectionPadding: "3px",
    enforceRadius: "none",
    enforceShadow: "none",
    buttonRadius: "0",
    buttonPadding: "",
    tableFontSize: "12px",
    tableCellPadding: "2px 5px",
    tableBorder: "bordered",
    tableBorderCollapse: "collapse",
    tableHeaderBg: "primary",
    tableZebra: "surface-alt",
    headerStyle: "primary",
    sidebarActiveStyle: "primary",
  },
};

export const THEME_NAMES: ThemeName[] = ["dark", "light", "retro"];
