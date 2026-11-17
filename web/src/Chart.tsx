import {useEffect,useRef} from 'react';
import * as echarts from 'echarts/core';
import {LineChart,BarChart} from 'echarts/charts';
import {GridComponent,TooltipComponent,ToolboxComponent,AriaComponent} from 'echarts/components';
import {CanvasRenderer} from 'echarts/renderers';
echarts.use([LineChart,BarChart,GridComponent,TooltipComponent,ToolboxComponent,AriaComponent,CanvasRenderer]);
export default function Chart({kind,items,dark}:{kind:'line'|'bar';items:{name:string;value:number|null}[];dark:boolean}){
 const ref=useRef<HTMLDivElement>(null);
 useEffect(()=>{const c=echarts.init(ref.current!);const horizontal=kind==='bar'&&items.some(i=>i.name.length>12);const categories={type:'category',data:items.map(i=>i.name),axisLabel:{width:135,overflow:'truncate'},inverse:horizontal};const values={type:'value',minInterval:1};c.setOption({aria:{enabled:true,label:{description:'Registros observados. '+items.map(i=>i.name+': '+(i.value===null?'sin información o valor protegido':i.value)).join('; ')}},color:['#0D9488'],textStyle:{color:dark?'#CBD5E1':'#475569'},grid:{left:horizontal?150:65,right:30,top:35,bottom:55},toolbox:{feature:{saveAsImage:{title:'Descargar imagen'}}},tooltip:{trigger:'axis',confine:true},xAxis:horizontal?values:categories,yAxis:horizontal?categories:values,series:[{type:kind,data:items.map(i=>i.value),connectNulls:false,smooth:false,areaStyle:kind==='line'?{opacity:.08}:undefined}]});const observer=new ResizeObserver(()=>c.resize());observer.observe(ref.current!);return()=>{observer.disconnect();c.dispose()}},[items,dark,kind]);
 return <><div ref={ref} className="chart" role="img" aria-label="Registros observados por categoría. Consulte la tabla equivalente."/><details><summary>Ver tabla accesible</summary><table><thead><tr><th>Categoría</th><th>Registros</th></tr></thead><tbody>{items.map(i=><tr key={i.name}><td>{i.name}</td><td>{i.value??'Sin información o protegido'}</td></tr>)}</tbody></table></details></>;
}
