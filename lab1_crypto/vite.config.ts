import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  root: "src/crypto_app/src",                 // index.html lives here
  server: { port: 5173, strictPort: true },
  build: {
    outDir: resolve(__dirname, "build/crypto_app/web"), // emit here for Lambda
    emptyOutDir: true,
    sourcemap: true,
    target: "es2022",
    manifest: true
  }
});
