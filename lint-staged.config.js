export default {
  '*.{js,jsx,ts,tsx,json,css,scss,md}': [
    'pnpm prettier --write',
    'pnpm eslint --fix',
  ],
  '**/Dockerfile*': [
    'hadolint',
  ],
  '*.md': [
    'markdownlint --fix',
  ],
};
