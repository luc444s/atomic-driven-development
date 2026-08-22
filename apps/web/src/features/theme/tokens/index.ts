import type { ThemeName, ThemeTokens } from "./types";
import { light } from "./light";
import { dark } from "./dark";
import { retro } from "./retro";

export type { ThemeName, ThemeTokens } from "./types";

export const themes: Record<ThemeName, ThemeTokens> = {
  light,
  dark,
  retro,
};

export const THEME_NAMES: ThemeName[] = ["dark", "light", "retro"];
