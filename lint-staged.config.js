export default {
  '*.{js,jsx,ts,tsx,json,css,scss,md}': (files) => {
    // Filter out files that should be ignored
    const filteredFiles = files.filter(file => 
      !file.includes('public/mockServiceWorker.js') &&
      !file.includes('playwright-report/') &&
      !file.includes('/dist/') &&
      !file.includes('/build/') &&
      !file.includes('/node_modules/')
    );
    
    if (filteredFiles.length === 0) return [];
    
    return [
      `pnpm prettier --write --ignore-unknown ${filteredFiles.join(' ')}`,
      `pnpm eslint --fix --no-error-on-unmatched-pattern ${filteredFiles.join(' ')}`,
    ];
  },
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
