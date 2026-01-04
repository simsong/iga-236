import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  root: "src/",                 // index.html lives here
  base: "/static/lab1_guesser/",
  server: {
    port: 5173,
    strictPort: true,
    open: "/static/lab1_guesser/index.html"
    },
  build: {
    outDir: resolve(__dirname, "../iga_236/home_app/static/lab1_guesser"),
    emptyOutDir: true,
    sourcemap: true,
    target: "es2022",
    manifest: true
  }
});
