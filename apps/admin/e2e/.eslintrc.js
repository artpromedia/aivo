import { defineConfig } from '@playwright/test'

// Playwright test files should have their own ESLint config
export default [
  {
    files: ['**/*.spec.ts', '**/*.test.ts'],
    languageOptions: {
      globals: {
        ...require('globals').browser,
        ...require('globals').node,
      },
    },
    rules: {
      'no-undef': 'off', // TypeScript handles this
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
]
