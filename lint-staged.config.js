export default {
  '*.{js,jsx,ts,tsx,json,css,scss,md}': [
    'pnpm prettier --write --ignore-unknown',
    'pnpm eslint --fix --no-error-on-unmatched-pattern',
  ],
  '**/Dockerfile*': [
    'hadolint',
  ],
  '*.md': (files) => {
    // Filter out SDK files and docs
    const filteredFiles = files.filter(file => 
      !file.includes('/docs/') && 
      !file.includes('libs/sdk-py/') && 
      !file.includes('libs/sdk-web/')
    );
    return filteredFiles.length > 0 ? 
      `markdownlint --fix ${filteredFiles.join(' ')}` : 
      [];
  },
};
