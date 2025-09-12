export default {
  '*.{js,jsx,ts,tsx,json,css,scss}': (files) => {
    // Filter out files that should be ignored (no markdown files here)
    const filteredFiles = files.filter(file => 
      !file.includes('public/mockServiceWorker.js') &&
      !file.includes('playwright-report/') &&
      !file.includes('/dist/') &&
      !file.includes('/build/') &&
      !file.includes('/node_modules/')
    );
    
    if (filteredFiles.length === 0) return [];
    
    // Split into smaller chunks to avoid command line length limits
    const chunkSize = 5;
    const chunks = [];
    for (let i = 0; i < filteredFiles.length; i += chunkSize) {
      chunks.push(filteredFiles.slice(i, i + chunkSize));
    }
    
    const commands = [];
    chunks.forEach(chunk => {
      commands.push(`npx prettier --write --ignore-unknown ${chunk.join(' ')}`);
      commands.push(`npx eslint --fix --no-error-on-unmatched-pattern ${chunk.join(' ')}`);
    });
    
    return commands;
  },
  '**/Dockerfile*': (files) => {
    // Skip Docker linting for now since hadolint is not installed
    return `echo "Skipping Docker linting (hadolint not installed)"`;
  },
  '*.md': (files) => {
    // Filter out SDK files and docs, and skip markdown linting for now
    const filteredFiles = files.filter(file => 
      !file.includes('/docs/') && 
      !file.includes('libs/sdk-py/') && 
      !file.includes('libs/sdk-web/')
    );
    
    if (filteredFiles.length === 0) return [];
    
    // Just run prettier on markdown files, skip markdownlint for now
    return [`npx prettier --write --ignore-unknown ${filteredFiles.join(' ')}`];
  },
};