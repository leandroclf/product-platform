export type ProductEventName='signup_completed'|'activation_completed'|'feature_used'|'limit_reached'|'upgrade_intent'|'subscription_changed'|'feedback_submitted';
export interface ProductEvent {schema_version:'1.0';event:ProductEventName;product_id:string;environment:string;release_sha:string;occurred_at:string;user_id?:string|null;account_id?:string|null;plan_id?:string|null;session_id?:string|null;feature?:string|null;outcome?:string|null}
export interface ProductEventSink{emit(event:ProductEvent):Promise<void>}
type Fields=Partial<Omit<ProductEvent,'schema_version'|'event'|'product_id'|'environment'|'release_sha'|'occurred_at'>>;
export function createProductEvents(config:{productId:string;sink:ProductEventSink;environment?:()=>string;releaseSha?:()=>string}){
 return {
  create(event:ProductEventName,fields:Fields={}):ProductEvent{return {...fields,schema_version:'1.0',event,product_id:config.productId,environment:config.environment?.()??'development',release_sha:config.releaseSha?.()??'local',occurred_at:new Date().toISOString()}},
  async emit(event:ProductEvent){try{await config.sink.emit(event)}catch(error){console.error('product_event_delivery_failed',error)}}
 };
}
