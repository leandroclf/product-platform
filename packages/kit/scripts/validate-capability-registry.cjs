const fs = require("fs");
const path = require("path");
const root = path.resolve(__dirname, "..");
const read = file => fs.readFileSync(path.join(root, file), "utf8");
const ownership = read("ARCHITECTURE-OWNERSHIP.yaml");
const registry = read("contracts/capability-registry.yaml");
const boundaries = read("contracts/repository-boundaries.yaml");

const portfolio = JSON.parse(read("contracts/portfolio-products.json"));
const required = [...portfolio.platform_repositories, ...portfolio.products.map(p => p.repository)];
if (portfolio.products.length !== 8 || new Set(required).size !== 12) throw new Error("portfolio must contain four platforms and eight unique products");
for (const repo of required) {
  if (!ownership.includes(repo)) throw new Error(`ownership missing repository: ${repo}`);
  if (!boundaries.includes(`  ${repo}:`)) throw new Error(`dependency boundary missing: ${repo}`);
}
for (const product of portfolio.products) {
  const domain = registry.split(`  ${product.domain}:\n`)[1]?.split(/\n  \S/)[0];
  if (!domain?.includes(`owner: ${product.repository}`)) throw new Error(`domain ownership missing: ${product.domain}`);
  if (!boundaries.includes(`  ${product.repository}: [product-platform-kit, product-platform-harness]`)) throw new Error(`product boundary drift: ${product.repository}`);
}
for (const token of ["default_decision_order: [reuse, extend, create]", "owner: product-platform-harness", "owner: product-platform-cli", "owner: product-platform-engineering-team"]) {
  if (!registry.includes(token)) throw new Error(`capability registry invariant missing: ${token}`);
}
if (!boundaries.includes("vehicle-tracking: [product-platform-kit, product-platform-harness]")) throw new Error("vehicle-tracking dependency boundary is stale");
if (/stripe_adapter:\s*\{\s*owner:\s*vehicle-tracking/.test(ownership)) throw new Error("Stripe adapter cannot be product-owned");
if (/mercado_pago_adapter:\s*\{\s*owner:\s*vehicle-tracking/.test(ownership)) throw new Error("Mercado Pago adapter cannot be product-owned");
console.log("Portfolio capability registry conformance: OK");
