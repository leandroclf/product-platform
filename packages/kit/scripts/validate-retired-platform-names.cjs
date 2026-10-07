const fs = require("fs");
const path = require("path");
const retired = ["ai-kit", "ai-engineering-team", "OmniCLI", "product-harness"];
const roots = ["ARCHITECTURE-OWNERSHIP.yaml", "contracts", "docs"];
const files = [];
function walk(p) {
  if (!fs.existsSync(p)) return;
  const stat = fs.statSync(p);
  if (stat.isFile()) { files.push(p); return; }
  for (const name of fs.readdirSync(p)) walk(path.join(p, name));
}
for (const root of roots) walk(root);
const violations = [];
for (const file of files) {
  const content = fs.readFileSync(file, "utf8");
  for (const name of retired) {
    if (content.includes(name) && !content.includes("product-platform-" + name)) {
      violations.push(file + ": " + name);
    }
  }
}
if (violations.length) {
  console.error("Retired platform repository references found:\n" + violations.join("\n"));
  process.exit(1);
}
console.log("Retired platform repository name gate: OK");
