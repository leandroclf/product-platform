import type { ProductEvent } from './events.js';
export interface ProductEventSink { emit(event:ProductEvent):Promise<void>; }
export class CompositeProductEventSink implements ProductEventSink { constructor(private readonly sinks:readonly ProductEventSink[]){} async emit(event:ProductEvent):Promise<void>{await Promise.allSettled(this.sinks.map(s=>s.emit(event)));} }
