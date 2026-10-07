import crypto from 'node:crypto';
import type { IPaymentGateway, WebhookInput } from './gateway.js';
import type { ChargeInput, CustomerInput, GatewayRef, NormalizedPaymentEvent, SubscriptionInput } from './types.js';
import { gatewayFetch } from './http.js';

export class MercadoPagoAdapter implements IPaymentGateway {
  readonly name='mercado_pago' as const;
  constructor(private readonly accessToken:string,private readonly webhookSecret:string,private readonly backUrl:string){}
  private headers(idempotencyKey?:string):HeadersInit{return {authorization:'Bearer '+this.accessToken,'content-type':'application/json',...(idempotencyKey?{'X-Idempotency-Key':idempotencyKey}:{})};}
  async createCustomer(input:CustomerInput):Promise<GatewayRef>{
    const r=await gatewayFetch<any>('https://api.mercadopago.com/v1/customers',{method:'POST',headers:this.headers(),body:JSON.stringify({email:input.email,first_name:input.name,description:'tenant:'+input.tenantId})}); return {id:r.id};
  }
  async createSubscription(input:SubscriptionInput):Promise<GatewayRef>{
    const r=await gatewayFetch<any>('https://api.mercadopago.com/preapproval',{method:'POST',headers:this.headers(),body:JSON.stringify({preapproval_plan_id:input.planExternalId,payer_email:input.email,card_token_id:input.paymentToken,external_reference:input.tenantId,back_url:this.backUrl,status:input.paymentToken?'authorized':'pending'})}); return {id:r.id,status:r.status,checkoutUrl:r.init_point};
  }
  async processCharge(input:ChargeInput):Promise<GatewayRef>{
    if(!input.paymentMethodId)throw new Error('mercado_pago payment token is required for direct charges');
    const r=await gatewayFetch<any>('https://api.mercadopago.com/v1/payments',{method:'POST',headers:this.headers(input.idempotencyKey),body:JSON.stringify({transaction_amount:input.amountMinor/100,token:input.paymentMethodId,description:input.description,external_reference:input.tenantId})}); return {id:String(r.id),status:r.status};
  }
  async cancelSubscription(id:string):Promise<void>{await gatewayFetch('https://api.mercadopago.com/preapproval/'+encodeURIComponent(id),{method:'PUT',headers:this.headers(),body:JSON.stringify({status:'canceled'})});}
  async verifyWebhook({headers,url}:WebhookInput):Promise<boolean>{
    const signature=headers.get('x-signature'),requestId=headers.get('x-request-id'),dataId=url.searchParams.get('data.id'); if(!signature||!requestId||!dataId)return false;
    const entries=signature.split(',').map(v=>v.trim().split('=',2)); const ts=entries.find(x=>x[0]==='ts')?.[1]; const v1=entries.find(x=>x[0]==='v1')?.[1]; if(!ts||!v1)return false;
    const manifest='id:'+dataId.toLowerCase()+';request-id:'+requestId+';ts:'+ts+';'; const expected=crypto.createHmac('sha256',this.webhookSecret).update(manifest).digest('hex'); const a=Buffer.from(expected,'hex'),b=Buffer.from(v1,'hex');
    return a.length===b.length&&crypto.timingSafeEqual(a,b);
  }
  async normalizeWebhook(input:WebhookInput):Promise<NormalizedPaymentEvent>{
    const e=JSON.parse(input.rawBody),resourceId=String(e.data?.id||''); const type=String(e.type||'').includes('preapproval')?'subscription':'payment'; let resource:any={};
    if(resourceId){const path=type==='subscription'?'preapproval/'+resourceId:'v1/payments/'+resourceId;resource=await gatewayFetch<any>('https://api.mercadopago.com/'+path,{headers:this.headers()});}
    const map:Record<string,string>={approved:'paid',authorized:'active',pending:'pending',rejected:'failed',cancelled:'canceled',canceled:'canceled',paused:'paused'};
    return {idempotencyKey:'mercado_pago:'+(e.id||e.action)+':'+resourceId,gateway:this.name,externalEventId:String(e.id||e.action),externalResourceId:resourceId,type,action:String(e.action||e.type),status:(map[resource.status]||'unknown') as any,amountMinor:resource.transaction_amount?Math.round(resource.transaction_amount*100):undefined,currency:resource.currency_id,tenantId:resource.external_reference,occurredAt:e.date_created||new Date().toISOString(),rawType:e.type};
  }
}
