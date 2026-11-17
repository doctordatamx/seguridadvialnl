import {useEffect,useMemo,useRef,useState} from 'react';
import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import type {FeatureCollection,Polygon} from 'geojson';
import type {Zone} from './intelligenceTypes';
import {circleGeometry} from './lib/geo';
import 'maplibre-gl/dist/maplibre-gl.css';
maplibregl.setWorkerUrl(workerUrl);
type CellProperties={cell:string;municipality:string;year:string;crashes:number;value?:number|null};
type Props={dark:boolean;year:string;municipality:string;publicEdition?:boolean;focusCell?:string;zones?:Zone[];metric?:string;alerts?:string[];boundaries?:FeatureCollection;institutions?:FeatureCollection;mobility?:FeatureCollection;onPick?:(point:number[])=>void;focusPoint?:number[]|null;radius?:number};
const empty:FeatureCollection={type:'FeatureCollection',features:[]};
export default function TerritorialMap({dark,year,municipality,publicEdition=false,focusCell,zones,metric='frequency',alerts,boundaries,institutions,mobility,onPick,focusPoint,radius=500}:Props){
 const threshold=publicEdition?20:10;
 const ref=useRef<HTMLDivElement>(null),mapRef=useRef<maplibregl.Map|null>(null),pickRef=useRef(onPick);
 const [data,setData]=useState<FeatureCollection<Polygon,CellProperties>|null>(null),[error,setError]=useState(''),[opacity,setOpacity]=useState(.75),[layer,setLayer]=useState('hexagons'),[loaded,setLoaded]=useState(false);
 pickRef.current=onPick;
 useEffect(()=>{let active=true;fetch(import.meta.env.BASE_URL+'data/spatial.json').then(r=>{if(!r.ok)throw Error('Capa espacial no disponible');return r.json()}).then(d=>{if(active)setData(d)}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[]);
 const filtered=useMemo<FeatureCollection<Polygon,CellProperties>>(()=>({type:'FeatureCollection',features:(data?.features??[]).filter(f=>(!year||f.properties.year===year)&&f.properties.municipality===(metric==='frequency'?(municipality||'Conjunto observado'):'Conjunto observado')&&(!focusCell||f.properties.cell===focusCell)&&(metric==='frequency'||!municipality||!!zones?.some(z=>z.cell===f.properties.cell&&z.municipalities.includes(municipality)))).map(f=>{
  const z=zones?.find(z=>z.cell===f.properties.cell);let value:number|null=f.properties.crashes;
  if(metric==='score')value=z?.score??null;else if(metric==='radar')value=alerts?.includes('h3-r7-'+f.properties.cell)?1:0;else if(metric!=='frequency')value=z?.metrics[metric]??null;
  return {...f,properties:{...f.properties,municipality:metric==='frequency'?f.properties.municipality:(z?.municipalities.join(' / ')??'Conjunto observado'),value}};
 }).filter(f=>metric==='frequency'||metric==='score'||(f.properties.value!==null&&f.properties.value!>0))}),[data,year,municipality,focusCell,zones,metric,alerts]);
 const ready=!!year&&filtered.features.length>0;
 useEffect(()=>{if(metric!=='frequency')setLayer('hexagons')},[metric]);
 useEffect(()=>{
  if(!ref.current)return;setLoaded(false);setError('');let map:maplibregl.Map;
  try{map=new maplibregl.Map({container:ref.current,center:[-100.3,25.7],zoom:9,style:{version:8,sources:{},layers:[{id:'background',type:'background',paint:{'background-color':dark?'#18334D':'#e3edf1'}}]},attributionControl:false});mapRef.current=map;
   map.addControl(new maplibregl.NavigationControl());map.addControl(new maplibregl.ScaleControl());
   map.addControl(new maplibregl.AttributionControl({customAttribution:['OCISEVI · RATIV · H3 provisional','Fuente: INEGI · Marco Geoestadístico 2025','© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap contributors · ODbL</a>']}));
   map.on('error',()=>setError('No fue posible renderizar una capa. Consulta las tablas y verifica WebGL.'));
   map.on('load',()=>{
    for(const id of ['cells','centers','boundaries','institutions','mobility','query'])map.addSource(id,{type:'geojson',data:empty});
    map.addLayer({id:'boundaries',type:'line',source:'boundaries',paint:{'line-color':dark?'#a2b5c8':'#536f83','line-width':1,'line-opacity':.65}});
    map.addLayer({id:'roads',type:'line',source:'mobility',filter:['==',['geometry-type'],'LineString'],paint:{'line-color':['match',['get','category'],'cycling','#a855f7','#67899b'],'line-width':2,'line-opacity':.7}});
    map.addLayer({id:'hexagons',type:'fill',source:'cells',paint:{'fill-color':'#0d9488','fill-opacity':.75,'fill-outline-color':dark?'#85d6d2':'#357978'}});
    map.addLayer({id:'heat',type:'heatmap',source:'centers',paint:{'heatmap-weight':['interpolate',['linear'],['get','crashes'],10,.1,300,1],'heatmap-radius':30,'heatmap-opacity':.75}});
    map.addLayer({id:'institutions',type:'circle',source:'institutions',paint:{'circle-radius':5,'circle-color':['match',['get','category'],'hospital','#dc2626','university','#f59e0b','#18334d'],'circle-stroke-color':'#fff','circle-stroke-width':1}});
    map.addLayer({id:'transit',type:'circle',source:'mobility',filter:['==',['geometry-type'],'Point'],paint:{'circle-color':'#0284c7','circle-radius':3}});
    map.addLayer({id:'query-fill',type:'fill',source:'query',paint:{'fill-color':'#38bdf8','fill-opacity':.1}});
    map.addLayer({id:'query-line',type:'line',source:'query',paint:{'line-color':'#0284c7','line-width':2,'line-dasharray':[3,2]}});
    setLoaded(true);
   });
   map.on('click',e=>pickRef.current?.([e.lngLat.lng,e.lngLat.lat]));
   map.on('click','hexagons',e=>{
    if(pickRef.current)return;const p=e.features?.[0].properties;if(!p)return;
    const box=document.createElement('div');box.style.color='#0b1728';const title=document.createElement('strong');title.textContent=p.municipality+' · '+p.year;
    const detail=document.createElement('p');detail.textContent=new Intl.NumberFormat('es-MX').format(p.crashes)+' registros · H3 '+p.cell;
    const link=document.createElement('a');link.textContent='Abrir ficha de referencia si existe';link.href='#ficha/h3-r7-'+p.cell;link.style.textDecoration='underline';
    const note=document.createElement('p');note.textContent='Valor de capa: '+(p.value===null?'No calculable':p.value)+'. Exploratorio, no riesgo.';
    box.append(title,detail,link,note);new maplibregl.Popup().setLngLat(e.lngLat).setDOMContent(box).addTo(map);
   });
   map.on('click','institutions',e=>{const p=e.features?.[0].properties;if(!p)return;const box=document.createElement('div');box.style.color='#0b1728';box.textContent=p.name+' · OpenStreetMap. No implica asociación causal con siniestros.';new maplibregl.Popup().setLngLat(e.lngLat).setDOMContent(box).addTo(map)});
  }catch{setError('WebGL no disponible. Consulta las tablas de agregados.');return}
  return()=>{map.remove();mapRef.current=null};
 },[dark]);
 useEffect(()=>{
  const m=mapRef.current;if(!loaded||!m)return;
  const collection=ready?filtered:{type:'FeatureCollection' as const,features:[]};
  (m.getSource('cells') as maplibregl.GeoJSONSource).setData(collection);
  (m.getSource('centers') as maplibregl.GeoJSONSource).setData({type:'FeatureCollection',features:collection.features.map(f=>{const vertices=f.geometry.coordinates[0].slice(0,-1);return {type:'Feature',properties:f.properties,geometry:{type:'Point',coordinates:[vertices.reduce((s,p)=>s+p[0],0)/vertices.length,vertices.reduce((s,p)=>s+p[1],0)/vertices.length]}}})});
  m.setPaintProperty('hexagons','fill-color',metric==='score'?['case',['==',['get','value'],null],'#94a3b8',['step',['get','value'],'#0d9488',25,'#38bdf8',50,'#f59e0b',75,'#dc2626']]:metric==='radar'?'#dc2626':['interpolate',['linear'],['coalesce',['get','value'],0],0,'#b7e4e0',metric==='frequency'?50:5,'#0d9488',metric==='frequency'?200:20,'#07585a',metric==='frequency'?500:100,'#f59e0b']);
  if(ready&&!focusPoint){const b=new maplibregl.LngLatBounds();for(const f of filtered.features)for(const p of f.geometry.coordinates[0])b.extend([p[0],p[1]]);m.fitBounds(b,{padding:45,maxZoom:focusCell?13:12,duration:0})}
 },[loaded,filtered,ready,metric,focusPoint,focusCell]);
 useEffect(()=>{const m=mapRef.current;if(!loaded||!m)return;
  for(const [id,collection] of [['boundaries',boundaries],['institutions',institutions],['mobility',mobility]] as const)(m.getSource(id) as maplibregl.GeoJSONSource).setData(collection??empty);
 },[loaded,boundaries,institutions,mobility]);
 useEffect(()=>{const m=mapRef.current;if(!loaded||!m)return;
  (m.getSource('query') as maplibregl.GeoJSONSource).setData(focusPoint?{type:'FeatureCollection',features:[circleGeometry(focusPoint,radius)]}:empty);
  if(focusPoint){const ring=circleGeometry(focusPoint,radius).geometry.coordinates[0];const b=new maplibregl.LngLatBounds();for(const p of ring)b.extend([p[0],p[1]]);m.fitBounds(b,{padding:50,maxZoom:15,duration:0})}
 },[loaded,focusPoint,radius]);
 useEffect(()=>{const m=mapRef.current;if(!loaded||!m)return;m.setPaintProperty('hexagons','fill-opacity',opacity);m.setPaintProperty('heat','heatmap-opacity',opacity);m.setLayoutProperty('hexagons','visibility',layer==='hexagons'?'visible':'none');m.setLayoutProperty('heat','visibility',layer==='heat'?'visible':'none')},[loaded,opacity,layer]);
 const top=ready?[...filtered.features].sort((a,b)=>b.properties.crashes-a.properties.crashes).slice(0,10):[];
 return <><div className="map-tools"><label>Representación<select value={layer} disabled={metric!=='frequency'} onChange={e=>setLayer(e.target.value)}><option value="hexagons">Hexágonos H3 · resolución {publicEdition?7:8}</option><option value="heat">Calor desde centroides H3</option></select></label><label>Opacidad · {Math.round(opacity*100)} %<input type="range" min=".2" max="1" step=".05" value={opacity} onChange={e=>setOpacity(+e.target.value)}/></label><span>{ready?filtered.features.length+' celdas · umbral fuente ≥'+threshold:!year?'Selecciona un año':'Sin celdas publicables'}</span></div>{error&&<p role="alert">{error}</p>}<div className="map-container"><div ref={ref} className="map" role="region" aria-label="Atlas exploratorio de agregados H3 y capas de contexto"/>{!ready&&<div className="map-overlay"><strong>{!year?'Selecciona un año':'Sin celdas disponibles'}</strong><p>No se completan ni geocodifican ubicaciones faltantes.</p></div>}<div className="map-legend"><strong>{metric==='score'?'IPIV experimental':metric==='frequency'?'Registros por hexágono':'Valor de la capa'}</strong><span className="legend-gradient"/><span>{metric==='score'?'0 · 25 · 50 · 75 · 100 · gris: incompleto':metric==='frequency'?threshold+' · 50 · 200 · 500+':'Sólo valores positivos publicables'}</span></div></div><p className="panel-foot">RATIV: datum y precisión sin declarar. INEGI: límites simplificados, no delimitación legal. OSM: inventario comunitario, no exhaustivo. Calor desde centroides, no puntos individuales. Proximidad no prueba causalidad.</p>{top.length>0&&<details><summary>Top 10 de celdas visibles · tabla accesible</summary><table><thead><tr><th>Celda/ficha</th><th>Municipio</th><th>Registros</th></tr></thead><tbody>{top.map(f=><tr key={f.properties.cell+f.properties.municipality}><td><a href={'#ficha/h3-r7-'+f.properties.cell}>{f.properties.cell}</a></td><td>{f.properties.municipality}</td><td>{f.properties.crashes}</td></tr>)}</tbody></table></details>}</>;
}
