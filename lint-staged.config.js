export default {
  '*.{js,jsx,ts,tsx,json,css,scss,md}': [
    'pnpm prettier --write --ignore-unknown',
    'pnpm eslint --fix --no-error-on-unmatched-pattern',
  ],
  '**/Dockerfile*': [
    'hadolint',
  ],
  '*.md': [
    'markdownlint --fix --ignore-path .gitignore',
  ],
};
