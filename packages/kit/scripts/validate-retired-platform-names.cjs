const fs = require("fs");
const path = require("path");
const retired = ["ai-kit", "ai-engineering-team", "OmniCLI", "product-harness"];
const root = path.resolve(__dirname, '..');
const roots = ["ARCHITECTURE-OWNERSHIP.yaml", "contracts", "docs"];
function findRetiredNames(file, content) {
  file = file.replace(/\\/g, '/');
  // These two files are immutable execution evidence, not current instructions.
  if (/^docs\/evolution\/(?:baseline-before|verification-after)\.json$/.test(file)) return [];
  // Installed command/config identifiers remain supported; do not rename them.
  content = content.replace(/(?<![\w/.-])(?:scripts\/ai-kit|ai-kit\.yaml)(?![\w/.-])/g, 'compatibility-identifier');
  if (file === 'docs/LEGACY-CUTOVER-GATE.md') {
    for (const [oldName, canonical] of Object.entries({ 'ai-kit': 'product-platform-kit', 'ai-engineering-team': 'product-platform-engineering-team', OmniCLI: 'product-platform-cli', 'product-harness': 'product-platform-harness' })) {
      content = content.split('\n').filter(line => line.trim() !== `| ${oldName} | ${canonical} |`).join('\n');
    }
  }
  // Preserve the public schema identifier, but not other old-name references.
  if (file === 'contracts/payment-event/v1.schema.json') {
    content = content.replace(/"\$id"\s*:\s*"https:\/\/ai-kit\/contracts\/payment-event\/v1\.schema\.json"/, '"$id":"legacy-schema-identity"');
  }
  return retired.filter(name => content.includes(name));
}
module.exports = { findRetiredNames };
if (require.main === module) {
const files = [];
function walk(p) {
  if (!fs.existsSync(p)) return;
  const stat = fs.statSync(p);
  if (stat.isFile()) { files.push(p); return; }
  for (const name of fs.readdirSync(p)) walk(path.join(p, name));
}
for (const entry of roots) walk(path.join(root, entry));
const violations = [];
for (const file of files) {
  const content = fs.readFileSync(file, "utf8");
  const relative = path.relative(root, file);
  for (const name of findRetiredNames(relative, content)) violations.push(relative + ": " + name);
}
if (violations.length) {
  console.error("Retired platform repository references found:\n" + violations.join("\n"));
  process.exit(1);
}
console.log("Retired platform repository name gate: OK");
}
