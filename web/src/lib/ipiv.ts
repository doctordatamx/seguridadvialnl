export const dimensions=['frequency','mortality','injuries','trend','vulnerable'] as const;
export type Dimension=typeof dimensions[number];
export type Components=Record<Dimension,number|null>;
export type Weights=Record<Dimension,number>;
export const defaultWeights:Weights={frequency:30,mortality:30,injuries:20,trend:10,vulnerable:10};
export function score(components:Components,weights:Weights):number|null{
 if(dimensions.some(d=>components[d]===null||!Number.isFinite(components[d])))return null;
 const total=dimensions.reduce((sum,d)=>sum+weights[d],0);
 if(!Number.isFinite(total)||total<=0||dimensions.some(d=>!Number.isFinite(weights[d])||weights[d]<0))return null;
 return dimensions.reduce((sum,d)=>sum+components[d]!*weights[d],0)/total;
}
export function priority(value:number|null):string{return value===null?'No calculable':value<25?'Baja':value<50?'Moderada':value<75?'Alta':'Muy alta'}
