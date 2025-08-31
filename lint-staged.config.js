module.exports = {
  '*.{js,jsx,ts,tsx,json,css,scss,md}': [
    'prettier --write',
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
