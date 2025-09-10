// Playwright test files should have their own ESLint config
import globals from 'globals';

export default [
  {
    files: ['**/*.spec.ts', '**/*.test.ts'],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    rules: {
      'no-undef': 'off', // TypeScript handles this
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
]
