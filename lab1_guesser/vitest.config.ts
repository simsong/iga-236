import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  test: {
    environment: "jsdom",
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html", "lcov"],
      include: ["src/**/*.ts"],
      exclude: ["src/**/*.test.ts", "node_modules/**"]
    }
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src")
    }
  }
});

