import { execSync } from "node:child_process";

try {
  const v = execSync("node -e \"console.log(require('eslint/package.json').version)\"")
    .toString()
    .trim();
  const major = parseInt(v.split('.')[0], 10);

  if (major < 9) {
    console.error(`ESLint ${v} detected; require >=9`);
    process.exit(1);
  }

  console.log(`ESLint ${v} OK`);
} catch (error) {
  console.error('Failed to check ESLint version:', error.message);
  process.exit(1);
}
