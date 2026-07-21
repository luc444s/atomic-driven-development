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

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@systutor/sdk/frontend": path.resolve(__dirname, "../../packages/sdk/frontend/index.ts"),
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
