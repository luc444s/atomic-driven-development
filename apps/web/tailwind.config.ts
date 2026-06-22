import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "rgb(51 65 85)",
        panel: "rgb(15 23 42)",
        panelAlt: "rgb(30 41 59)",
      },
    },
  },
  plugins: [],
} satisfies Config;
