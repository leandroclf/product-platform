export interface ProductIdentity { productId:string; environment:string; releaseSha:string; userId?:string|null; accountId?:string|null; planId?:string|null; sessionId?:string|null; }
export function requireAccount(identity:ProductIdentity):string { if(!identity.accountId) throw new Error('account_id is required'); return identity.accountId; }
