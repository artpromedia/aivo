#!/usr/bin/env node
import fs from "node:fs";
import { execSync } from "node:child_process";

const lock = fs.readFileSync("pnpm-lock.yaml", "utf8");

// Extract packages from the packages section and dependencies section
const packages = new Set();

// Get packages from the packages section (e.g., "/lodash@4.17.21:")
for (const match of lock.matchAll(/^\s*\/([^@\s]+)@([^:\s]+):/gm)) {
  packages.add(`${match[1]}@${match[2]}`);
}

// Get packages from the packages section (e.g., "lodash@4.17.21:")  
for (const match of lock.matchAll(/^\s*([^@\/\s]+)@([^:\s]+):/gm)) {
  packages.add(`${match[1]}@${match[2]}`);
}

// Also extract from name/version pairs in package definitions
for (const match of lock.matchAll(/\s+name: ([^@\s][^\n]+)\n\s+version: ([^\n]+)/g)) {
  packages.add(`${match[1]}@${match[2]}`);
}

const pkgs = [...packages];

let bad = [];
for (const id of pkgs) {
  try {
    const out = execSync(`npm view ${id} deprecated --json`, { stdio: ["ignore","pipe","pipe"] })
      .toString().trim();
    if (out && out !== "null" && out !== "false" && out !== "undefined") bad.push({ id, msg: out });
  } catch { /* ignore missing */ }
}
if (bad.length) {
  console.error("Deprecated packages detected:");
  for (const b of bad) console.error(`- ${b.id}: ${b.msg}`);
  process.exit(1);
}
console.log(`No deprecated packages across ${pkgs.length} locked entries.`);
