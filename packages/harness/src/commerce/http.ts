export function formBody(values:Record<string,unknown>):string { const body=new URLSearchParams(); for(const [k,v] of Object.entries(values)) if(v!==undefined&&v!==null) body.set(k,String(v)); return body.toString(); }
export async function gatewayFetch<T=unknown>(url:string,init:RequestInit={}):Promise<T>{
  // A timeout is an ambiguous write outcome, never permission to retry with a new key.
  const timeout=AbortSignal.timeout(15_000);
  const signal=init.signal?AbortSignal.any([init.signal,timeout]):timeout;
  const r=await fetch(url,{...init,signal});
  if(!r.ok)throw new Error(`payment gateway request failed (${r.status})`);
  if(r.status===204)return undefined as T;
  return await r.json() as T;
}
