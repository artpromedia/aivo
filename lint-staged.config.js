module.exports = {
  '*.{js,jsx,ts,tsx,json,css,scss,md}': [
    'prettier --write',
    'eslint --fix',
  ],
  '*.{yml,yaml}': [
    'yamllint -s',
  ],
  '**/Dockerfile*': [
    'hadolint',
  ],
  '*.md': [
    'markdownlint --fix',
  ],
};
