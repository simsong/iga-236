import js from "@eslint/js";
import tseslint from "@typescript-eslint/eslint-plugin";
import tsparser from "@typescript-eslint/parser";
import globals from "globals";

export default [
  js.configs.recommended,
  {
    files: ["**/*.ts", "**/*.js"],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: "module",
        project: "./tsconfig.json"
      },
      globals: {
        ...globals.browser
      }
    },
    plugins: {
      "@typescript-eslint": tseslint
    },
    rules: {
      ...tseslint.configs.recommended.rules,
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
      "no-undef": "off" // TypeScript handles this
    }
  },
  {
    files: ["**/pgpWorker.ts"],
    languageOptions: {
      globals: {
        ...globals.worker
      }
    }
  },
  {
    ignores: [
      "node_modules/**",
      "build/**",
      "coverage/**",
      "dist/**",
      "*.min.js",
      "*.bundle.js",
      "**/*.html" // HTML files are linted separately with djlint
    ]
  }
];

