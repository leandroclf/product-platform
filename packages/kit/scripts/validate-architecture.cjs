#!/usr/bin/env node
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..');
const schema=JSON.parse(fs.readFileSync(path.join(root,'contracts/product-event/v1.schema.json'),'utf8'));
for(const k of ['schema_version','event','product_id','environment','release_sha','occurred_at']) if(!schema.required.includes(k)) throw new Error('missing '+k);
if(schema.additionalProperties!==false) throw new Error('additionalProperties must be false');
for(const k of ['email','phone','name','gps','imei','plate','vin','token','cpf','cnpj']) if(schema.properties[k]) throw new Error('forbidden PII '+k);
const ownership=fs.readFileSync(path.join(root,'ARCHITECTURE-OWNERSHIP.yaml'),'utf8');
for(const rule of ['shared_contracts: { owner: product-platform-kit','engineering_orchestration: { owner: product-platform-engineering-team','proposal_generation: { owner: product-platform-cli']) if(!ownership.includes(rule)) throw new Error('ownership drift: '+rule);
require('./validate-capability-registry.cjs');
const { execFileSync } = require('child_process');
execFileSync(process.execPath, [path.join(__dirname, 'validate-retired-platform-names.cjs')], { stdio: 'inherit' });
execFileSync(process.execPath, ['--test', path.join(__dirname, 'validate-retired-platform-names.test.cjs')], { stdio: 'inherit' });
console.log('architecture and contract conformance: OK');
