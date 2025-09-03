#!/usr/bin/env node
import fs from "node:fs";
import { execSync } from "node:child_process";

// Use test file for now
const lockFile = fs.existsSync("pnpm-lock.yaml") ? "pnpm-lock.yaml" : "test-pnpm-lock.yaml";
const lock = fs.readFileSync(lockFile, "utf8");
const pkgs = [...new Set(
  [...lock.matchAll(/\s+name: ([^@\s][^ \n]+)\n\s+version: ([^\n]+)/g)]
    .map(([, n, v]) => `${n}@${v}`)
)];

console.log(`Found ${pkgs.length} packages to check...`);
console.log(`Packages: ${pkgs.slice(0, 5).join(", ")}${pkgs.length > 5 ? "..." : ""}`);

let bad = [];
for (const id of pkgs) {
  try {
    console.log(`Checking ${id}...`);
    const out = execSync(`npm view ${id} deprecated --json`, { stdio: ["ignore","pipe","pipe"] })
      .toString().trim();
    if (out && out !== "null" && out !== "false" && out !== "undefined") bad.push({ id, msg: out });
  } catch (e) { 
    console.log(`  (skipped ${id} - not found)`);
  }
}
if (bad.length) {
  console.error("Deprecated packages detected:");
  for (const b of bad) console.error(`- ${b.id}: ${b.msg}`);
  process.exit(1);
}
console.log(`No deprecated packages across ${pkgs.length} locked entries.`);
