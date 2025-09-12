// Playwright test files should have their own ESLint config
const globals = require('globals');

module.exports = [
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
