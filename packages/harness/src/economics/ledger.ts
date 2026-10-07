export interface LedgerEntry { id:string; accountId:string; gateway:string; currency:string; grossMinor:number; feeMinor:number; taxMinor:number; netMinor:number; occurredAt:string; }
export function validateLedgerEntry(entry:LedgerEntry):LedgerEntry { if(entry.grossMinor-entry.feeMinor-entry.taxMinor!==entry.netMinor)throw new Error('invalid ledger economics'); return entry; }
