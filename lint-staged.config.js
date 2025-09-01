module.exports = {
  '*.{js,jsx,ts,tsx,json,css,scss,md}': [
    'pnpm prettier --write',
    'pnpm eslint --fix',
  ],
  '*.{yml,yaml}': [
    'pnpm yamllint -s',
  ],
  '**/Dockerfile*': [
    'hadolint',
  ],
  '*.md': [
    'markdownlint --fix',
  ],
};
