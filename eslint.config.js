import js from "@eslint/js";
import tsParser from "@typescript-eslint/parser";
import tsPlugin from "@typescript-eslint/eslint-plugin";
import importPlugin from "eslint-plugin-import";
import unusedImportsPlugin from "eslint-plugin-unused-imports";

export default [
  js.configs.recommended,
  {
    files: ["**/*.{ts,tsx,cts,mts}"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        project: false,
        sourceType: "module",
        ecmaVersion: "latest"
      }
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
      "import": importPlugin,
      "unused-imports": unusedImportsPlugin
    },
    rules: {
      "no-unused-vars": "off",
      "@typescript-eslint/no-unused-vars": "off",
      "unused-imports/no-unused-imports": "error",
      "unused-imports/no-unused-vars": [
        "warn",
        {
          "vars": "all",
          "varsIgnorePattern": "^_",
          "args": "after-used",
          "argsIgnorePattern": "^_"
        }
      ],
      "import/order": [
        "error",
        {
          "newlines-between": "always",
          "groups": [
            "builtin",
            "external",
            "internal",
            "parent",
            "sibling",
            "index"
          ],
          "alphabetize": {
            "order": "asc",
            "caseInsensitive": true
          }
        }
      ],
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/explicit-function-return-type": "off",
      "@typescript-eslint/explicit-module-boundary-types": "off",
      "@typescript-eslint/no-inferrable-types": "error",
      "prefer-const": "error",
      "no-var": "error"
    }
  },
  {
    files: ["**/*.{js,jsx,cjs,mjs}"],
    rules: {
      "no-unused-vars": "error",
      "prefer-const": "error",
      "no-var": "error"
    }
  },
  {
    ignores: [
      "**/node_modules/**",
      "**/dist/**",
      "**/build/**",
      "**/.next/**",
      "**/.nuxt/**",
      "**/.output/**",
      "**/.vercel/**",
      "**/.netlify/**",
      "**/coverage/**",
      "**/*.config.{js,ts,mjs}",
      "**/*.d.ts",
      "**/.venv/**",
      "**/libs/sdk-web/**",
      "**/scripts/**"
    ]
  }
];
