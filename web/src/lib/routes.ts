const known=new Set(['panorama','mapa','criticos','ipiv','radar','temporal','municipios','vulnerables','salud','datos','informes','metodologia']);
export type Route={section:string;zoneId?:string};
export function parseHash(hash:string):Route|null{
 const value=hash.replace(/^#/,'');if(value==='content')return null;
 if(!value)return {section:'panorama'};
 const match=/^ficha\/(h3-r7-[0-9a-f]{15})$/.exec(value);
 if(match)return {section:'ficha',zoneId:match[1]};
 return {section:known.has(value)?value:'notfound'};
}
