const fs = require("fs");
const ownership = fs.readFileSync("ARCHITECTURE-OWNERSHIP.yaml", "utf8");
const registry = fs.readFileSync("contracts/capability-registry.yaml", "utf8");
const boundaries = fs.readFileSync("contracts/repository-boundaries.yaml", "utf8");

const required = ["OmniCLI", "ai-engineering-team", "ai-kit", "product-harness", "vehicle-tracking", "ai-docs", "bussola-financeira"];
for (const repo of required) {
  if (!ownership.includes(repo)) throw new Error(`ownership missing repository: ${repo}`);
}
for (const token of ["default_decision_order: [reuse, extend, create]", "owner: product-harness", "owner: OmniCLI", "owner: ai-engineering-team"]) {
  if (!registry.includes(token)) throw new Error(`capability registry invariant missing: ${token}`);
}
if (!boundaries.includes("vehicle-tracking: [ai-kit, product-harness]")) throw new Error("vehicle-tracking dependency boundary is stale");
if (/stripe_adapter:\s*\{\s*owner:\s*vehicle-tracking/.test(ownership)) throw new Error("Stripe adapter cannot be product-owned");
if (/mercado_pago_adapter:\s*\{\s*owner:\s*vehicle-tracking/.test(ownership)) throw new Error("Mercado Pago adapter cannot be product-owned");
console.log("Portfolio capability registry conformance: OK");
