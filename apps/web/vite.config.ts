import { defineConfig, searchForWorkspaceRoot } from "vite";
import react from "@vitejs/plugin-react";
import os from "os";
import path from "path";

function resolveLanHost() {
  for (const addresses of Object.values(os.networkInterfaces())) {
    for (const address of addresses ?? []) {
      if (address.family === "IPv4" && !address.internal) {
        return address.address;
      }
    }
  }

  return undefined;
}

const devPort = Number(process.env.VITE_DEV_PORT ?? "5173");
const hmrHost = process.env.VITE_HMR_HOST ?? resolveLanHost();

// Plugins y packages importan bare deps (react, leaflet, etc.) que viven
// en apps/web/node_modules. En dev, optimizeDeps los resuelve desde el
// root del proyecto; en build, rollup resuelve desde el importer
// (plugins/...) y no los encuentra. Los aliases fuerzan la resolucion.
const BARE_DEP_ALIASES = [
  "react",
  "react-dom",
  "react-dom/client",
  "react-dom/server",
  "react-router-dom",
  "@tanstack/react-query",
  "leaflet",
  "react-leaflet",
  "zustand",
  "lucide-react",
  "clsx",
  "tailwind-merge",
  "sonner",
  "@monaco-editor/react",
  "monaco-editor",
  "@react-pdf-viewer/core",
];

const nodeModulesAliases = Object.fromEntries(
  BARE_DEP_ALIASES.map((name) => [
    name,
    path.resolve(__dirname, `./node_modules/${name}`),
  ])
);

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@systutor/sdk/frontend": path.resolve(__dirname, "../../vendor/systutor-core/src/systutor/sdk/frontend/index.ts"),
      "@systutor/shell": path.resolve(__dirname, "../../vendor/systutor-shell/src"),
      "pdfjs-dist/build/pdf.worker.min.js?url": path.resolve(__dirname, "node_modules/pdfjs-dist/build/pdf.worker.min.js"),
      ...nodeModulesAliases,
    },
  },
  server: {
    port: devPort,
    host: true,
    strictPort: true,
    hmr: hmrHost
      ? {
          host: hmrHost,
          clientPort: devPort,
        }
      : undefined,
    fs: {
      allow: [searchForWorkspaceRoot(process.cwd())],
    },
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
