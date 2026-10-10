// vite.config.js - The dev server runs on http://localhost:3000.
// Requests to /api and /health are forwarded ("proxied") to the FastAPI backend,
// so the browser sees one address and we don't have to think about CORS.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": BACKEND,
      "/health": BACKEND,
    },
  },
});
