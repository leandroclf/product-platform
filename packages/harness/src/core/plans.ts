export interface PlanDefinition { id:string; capabilities:Record<string,number|null>; }
export interface PlanCatalog { get(planId:string):PlanDefinition|undefined; }
export class StaticPlanCatalog implements PlanCatalog { constructor(private readonly plans:readonly PlanDefinition[]){} get(planId:string){return this.plans.find(p=>p.id===planId);} }
