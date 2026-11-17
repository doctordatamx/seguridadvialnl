export type PolygonCell={geometry:{type:string;coordinates:number[][][]};properties:{cell:string;crashes:number;municipality:string;year:string}};
export function distanceMeters(a:number[],b:number[]):number{
 const rad=Math.PI/180;const p=(b[1]-a[1])*rad,q=(b[0]-a[0])*rad;
 const h=Math.sin(p/2)**2+Math.cos(a[1]*rad)*Math.cos(b[1]*rad)*Math.sin(q/2)**2;
 return 6371008.8*2*Math.atan2(Math.sqrt(Math.min(1,h)),Math.sqrt(Math.max(0,1-h)));
}
export function proximityBounds(cells:PolygonCell[],point:number[],radius:number){
 if(radius<=0||!Number.isFinite(radius)||point.length!==2||point.some(v=>!Number.isFinite(v))||Math.abs(point[0])>180||Math.abs(point[1])>90)throw Error('Consulta espacial inválida');
 let lower=0,upper=0,intersecting=0;
 for(const cell of cells){
  const ring=cell.geometry.coordinates[0].slice(0,-1);
  const center=[ring.reduce((s,p)=>s+p[0],0)/ring.length,ring.reduce((s,p)=>s+p[1],0)/ring.length];
  // Margen conservador para el modelo esférico y las aristas geográficas.
  const cover=Math.max(...ring.map(p=>distanceMeters(center,p)))*1.02+1;
  const d=distanceMeters(point,center);
  if(d+cover<=radius)lower+=cell.properties.crashes;
  if(d-cover<=radius){upper+=cell.properties.crashes;intersecting++}
 }
 return {lower,upper,intersecting,scope:'Sólo celdas agregadas visibles; no acota los registros ocultos o no localizados.'};
}
export function circleGeometry(point:number[],radius:number){
 const rad=Math.PI/180,lat=point[1]*rad,lon=point[0]*rad,d=radius/6371008.8;const ring:number[][]=[];
 for(let i=0;i<=64;i++){const angle=i/64*2*Math.PI;const y=Math.asin(Math.sin(lat)*Math.cos(d)+Math.cos(lat)*Math.sin(d)*Math.cos(angle));const x=lon+Math.atan2(Math.sin(angle)*Math.sin(d)*Math.cos(lat),Math.cos(d)-Math.sin(lat)*Math.sin(y));ring.push([x/rad,y/rad])}
 return {type:'Feature' as const,properties:{},geometry:{type:'Polygon' as const,coordinates:[ring]}};
}
