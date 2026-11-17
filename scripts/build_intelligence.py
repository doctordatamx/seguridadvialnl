"""Materializa inteligencia 0.2 desde Parquet local. Sólo publica agregados revisados."""
from __future__ import annotations
import argparse, hashlib, json, sys
from collections import Counter, defaultdict
from datetime import date,timedelta,datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import h3
import polars as pl
from pipelines.intelligence import fixed_reference,protected_counts,protected_spatial_counts,rate_comparison,bh_adjust,poisson_rate_interval,normalize_against,ipiv
from pipelines.rativ import protected_histogram

ROOT=Path(__file__).resolve().parents[1]


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')


def summed(rows,key):
    values=[r[key] for r in rows]
    return sum(values) if values and all(v is not None for v in values) else None


def stats(rows):
    known_deaths=all(r['deaths'] is not None for r in rows)
    known_victims=all(r['deaths'] is not None and r['injured'] is not None for r in rows)
    known_ped=all(r['pedestrian_deaths'] is not None and r['pedestrian_injured'] is not None for r in rows)
    return {'frequency':len(rows),'mortality':summed(rows,'deaths'),'injuries':summed(rows,'injured'),
            'fatal_records':sum(r['deaths']>0 for r in rows) if known_deaths else None,
            'victim_records':sum(r['deaths']>0 or r['injured']>0 for r in rows) if known_victims else None,
            'pedestrian_records':sum(r['pedestrian_deaths']>0 or r['pedestrian_injured']>0 for r in rows) if known_ped else None,
            'motorcycle_records':sum('Motocicleta' in (r['vulnerable_user'] or '') for r in rows),
            'bicycle_records':sum('Bicicleta' in (r['vulnerable_user'] or '') for r in rows),
            'vulnerable':sum(bool(r['vulnerable_user']) for r in rows)}


def temporal(rows):
    daily=Counter(r['date'] for r in rows);months=defaultdict(list)
    for day,count in sorted(daily.items()):months[day[:7]].append((day,count))
    calendar=[]
    for month,items in sorted(months.items()):
        for (day,count),value in zip(items,protected_counts([v for _,v in items])):
            calendar.append({'date':day,'value':value,'status':'suppressed' if value is None else 'observed'})
    matrix=Counter((r['weekday'],r['hour']) for r in rows if r['hour'] is not None)
    keys=sorted(matrix);values=protected_counts([matrix[k] for k in keys])
    return {'calendar':calendar,'matrix':[{'weekday':k[0],'hour':k[1],'value':v} for k,v in zip(keys,values)],
            'records':len(rows),'hour_known':sum(matrix.values())}


def build(records_path):
    frame=pl.read_parquet(records_path);rows=frame.to_dicts();cutoff=max(r['date'] for r in rows)
    by_municipal_year=defaultdict(list);by_cell_year=defaultdict(list);by_cell=defaultdict(list)
    for r in rows:
        r['_date']=date.fromisoformat(r['date']);year=r['date'][:4]
        by_municipal_year[(r['municipality'],year)].append(r)
        if r['latitude'] is not None:
            cell=h3.latlng_to_cell(r['latitude'],r['longitude'],7)
            by_cell_year[(cell,year)].append(r);by_cell[cell].append(r)
    reference_year='2025';previous_year='2024'
    cells=sorted(cell for cell,year in by_cell_year if year==reference_year and len(by_cell_year[(cell,year)])>=20 and len(by_cell_year.get((cell,previous_year),[]))>=20)
    zones=[];research=[]
    for cell in cells:
        current=by_cell_year[(cell,reference_year)];previous=by_cell_year[(cell,previous_year)]
        ref=current+previous;municipalities=Counter(r['municipality'] for r in ref)
        s=stats(current);base=stats(previous);lat,lon=h3.cell_to_latlng(cell)
        quality=[]
        for municipality in municipalities:
            proportions=[]
            for year in [previous_year,reference_year]:
                group=by_municipal_year[(municipality,year)]
                proportions.append(sum(r['latitude'] is not None for r in group)/len(group))
            quality.append(min(proportions)>=.95 and abs(proportions[0]-proportions[1])<=.025)
        comparable=all(quality)
        trend=(len(current)/len(previous)-1)*100 if comparable else None
        months=Counter(r['date'][:7] for r in by_cell[cell]);ordered=sorted(months)
        # No completar periodos sin registros con cero; sólo contar meses observados.
        monthly=[]
        for y in sorted({m[:4] for m in ordered}):
            family=[m for m in ordered if m.startswith(y)]
            monthly.extend({'name':month,'value':value} for month,value in zip(family,protected_counts([months[m] for m in family])))
        annual=[{'year':y,'records':len(g) if len(g)>=20 else None} for (c,y),g in sorted(by_cell_year.items()) if c==cell]
        zone={'id':'h3-r7-'+cell,'cell':cell,'name':'Celda '+cell[:9].upper(),'municipality':municipalities.most_common(1)[0][0],
              'municipalities':sorted(municipalities),'center':[lon,lat],'reference_year':reference_year,
              'dimensions':{d:(trend if d=='trend' else s[d]) for d in ['frequency','mortality','injuries','trend','vulnerable']},
              'metrics':s,'baseline_records':len(previous),'comparability':comparable,
              'clinical_status':{},'monthly':monthly,
              'annual':annual,'accumulated_records':sum(a['records'] for a in annual) if all(a['records'] is not None for a in annual) else None,
              'report_hour':protected_histogram(Counter(r['hour'] for r in current if r['hour'] is not None),5),
              'weekday':protected_histogram(Counter(r['weekday'] for r in current),5),
              'crash_types':protected_histogram(Counter(r['crash_type'] for r in current if r['crash_type']),5),
              'vehicles':protected_histogram(Counter(v for r in current for v in (r['vehicles'] or '').split('; ') if v),5),
              'hour_known':sum(r['hour'] is not None for r in current),
              'coordinates_status':'Centroide H3; no es ubicación de un evento. Datum RATIV sin confirmar.',
              'streets_status':'Texto libre no publicado; sin cruce validado con red vial.'}
        research.append({'id':zone['id'],'metrics':dict(s),'trend':trend})
        zones.append(zone)
    # Supresión primaria y complementaria ANTES de índices, ratios y normalizaciones públicos.
    protected_fields=['mortality','injuries','fatal_records','victim_records','pedestrian_records','motorcycle_records','bicycle_records','vulnerable']
    withheld_margins={}
    for field in protected_fields:
        safe,withheld=protected_spatial_counts([z['metrics'][field] for z in zones],[z['municipalities'] for z in zones])
        withheld_margins[(reference_year,field)]=withheld
        for z,value in zip(zones,safe):
            z['clinical_status'][field]='missing' if z['metrics'][field] is None else 'suppressed' if value is None else 'known'
            z['metrics'][field]=value
            if field in z['dimensions']:z['dimensions'][field]=value
    for z in zones:
        z['metrics']['severity']=z['metrics']['fatal_records']/z['metrics']['frequency']*100 if z['metrics']['fatal_records'] is not None else None
        z['history']=[{'year':'2024','score':None,'reason':'Geocobertura 2023 no comparable; sin dimensión de tendencia válida.'},
                      {'year':'2026','score':None,'reason':'Año parcial y cambio de geocobertura.'}]
    reference=fixed_reference(zones)
    signature=hashlib.sha256(json.dumps([(z['id'],z['dimensions']) for z in zones],sort_keys=True).encode()).hexdigest()[:10]
    reference.update({'id':'ipiv-experimental-2025-r7-v02-'+signature,'year':reference_year,'baseline_year':previous_year,'resolution':7,
                      'population_rule':'Todas las celdas R7 con >=20 registros en 2024 y en 2025; población fija, no cambia con filtros.',
                      'vulnerable_definition':'Registros con evidencia documentada de motocicleta, bicicleta o peatón lesionado/fallecido. Proxy de registro, no número de personas ni ausencia real de usuarios.',
                      'experimental':True,'thresholds':[25,50,75], 'interpretation':'Hipótesis de priorización para evaluación; no riesgo individual ni índice validado.'})
    historical=[]
    for z in zones:
        current=by_cell_year[(z['cell'],'2024')];previous=by_cell_year.get((z['cell'],'2023'),[])
        comparable=bool(previous) and len(previous)>=20
        for municipality in z['municipalities']:
            rates=[]
            for y in ['2023','2024']:
                group=by_municipal_year.get((municipality,y),[])
                rates.append(sum(r['latitude'] is not None for r in group)/len(group) if group else 0)
            comparable=comparable and min(rates)>=.95 and abs(rates[0]-rates[1])<=.025
        s=stats(current)
        historical.append({d:(len(current)/len(previous)*100-100 if comparable else None) if d=='trend' else s[d]
                           for d in ['frequency','mortality','injuries','trend','vulnerable']})
    for dim in ['mortality','injuries','vulnerable']:
        safe,withheld=protected_spatial_counts([h[dim] for h in historical],[z['municipalities'] for z in zones])
        withheld_margins[('2024',dim)]=withheld
        for h,value in zip(historical,safe):h[dim]=value
    calibrated=[{} for _ in zones]
    for dim in ['frequency','mortality','injuries','trend','vulnerable']:
        for h,value in zip(calibrated,normalize_against([h[dim] for h in historical],[z['dimensions'][dim] for z in zones])):h[dim]=value
    for z,h,norm in zip(zones,historical,calibrated):
        value=ipiv(norm)
        z['history'][0]={'year':'2024','score':value,'dimensions':h,'normalized':norm,
                         'reason':'Calibración fija 2025 aplicada a 2024; estimación retrospectiva, no score recalibrado.' if value is not None else 'No calculable: geocobertura/baseline 2023 no comparables o dimensión protegida/faltante.'}
    # Radar: ventana anclada al CORTE, no al día actual; cuatro contrastes por zona en una familia BH fija.
    end=date.fromisoformat(cutoff);radar=[]
    for zone in zones:
        members=zone['municipalities'];records=by_cell[zone['cell']]
        for days in [30,90,180,365]:
            start=end-timedelta(days=days-1);prior_end=end.replace(year=end.year-1);prior_start=start.replace(year=start.year-1)
            current=[r for r in records if start<=r['_date']<=end];previous=[r for r in records if prior_start<=r['_date']<=prior_end]
            coverage=[]
            for municipality in members:
                all_rows=[r for year in range(prior_start.year,end.year+1) for r in by_municipal_year.get((municipality,str(year)),[])]
                rates=[]
                for a,b in [(start,end),(prior_start,prior_end)]:
                    group=[r for r in all_rows if a<=r['_date']<=b]
                    rates.append(sum(r['latitude'] is not None for r in group)/len(group) if group else None)
                coverage.append(rates)
            comparable=bool(coverage) and all(a is not None and b is not None and min(a,b)>=.95 and abs(a-b)<=.025 for a,b in coverage)
            counts=[len(current),len(previous)];safe=protected_counts(counts)
            is_public=all(v is not None for v in safe)
            test=rate_comparison(*counts,days,(prior_end-prior_start).days+1,comparable and is_public)
            radar.append({'zone_id':zone['id'],'days':days,'start':start.isoformat(),'end':end.isoformat(),
                          'baseline_start':prior_start.isoformat(),'baseline_end':prior_end.isoformat(),
                          'current':safe[0],'previous':safe[1],'comparable_proxy':comparable,'coverage':coverage,**test})
    adjusted=bh_adjust([r['p_value'] for r in radar])
    for row,q in zip(radar,adjusted):
        row['q_value']=q;row['statistical_alert']=q is not None and q<.05 and row['ratio']>1
        row['classification']='Información insuficiente' if q is None else 'Emergentes' if row['statistical_alert'] and row['ratio']>=2 else 'En crecimiento' if row['statistical_alert'] else 'En disminución' if q<.05 and row['ratio']<1 else 'Estables'
    import numpy as np
    threshold_current=float(np.quantile([z['metrics']['frequency'] for z in zones],.9));threshold_previous=float(np.quantile([z['baseline_records'] for z in zones],.9))
    persistent={z['id'] for z in zones if z['metrics']['frequency']>=threshold_current and z['baseline_records']>=threshold_previous}
    for z in zones:z['persistent_high_frequency']=z['id'] in persistent
    for row in radar:
        if row['classification']=='Estables' and row['zone_id'] in persistent:row['classification']='Persistentemente críticos'
    # Epidemiología: sólo denominador 2020 verificado. No extrapolar a 2025/2026.
    census=json.loads((ROOT/'data/external/inegi_municipios_19.json').read_text(encoding='utf-8'))
    if '2020' not in census.get('metadatos',{}).get('Fuente_informacion_estadistica',''):
        raise ValueError('La fuente no declara Censo 2020; no se asigna un año de denominador supuesto.')
    populations={r['cve_mun']:int(r['pob_total']) for r in census['datos']}
    epidemiology=[]
    for (municipality,year),group in sorted(by_municipal_year.items()):
        values=stats(group);code=group[0]['municipality_code']
        epidemiology.append({'municipality':municipality,'year':year,'population':populations.get(code) if year=='2020' else None,
                             'population_year':2020 if year=='2020' else None,'metrics':values,
                             'statuses':{k:'missing' if v is None else 'known' for k,v in values.items()}})
    for year in sorted({r['year'] for r in epidemiology}):
        family=[r for r in epidemiology if r['year']==year]
        for field in ['mortality','injuries','fatal_records','victim_records','pedestrian_records','motorcycle_records','bicycle_records','vulnerable']:
            for row,value in zip(family,protected_counts([r['metrics'][field] for r in family])):
                if value is None and row['metrics'][field] is not None:row['statuses'][field]='suppressed'
                row['metrics'][field]=value
    for row in epidemiology:
        for field in ['mortality','injuries','fatal_records','victim_records','pedestrian_records','motorcycle_records','bicycle_records','vulnerable']:
            if row['municipality'] in withheld_margins.get((row['year'],field),set()):
                row['metrics'][field]=None;row['statuses'][field]='withheld_geographic_margin'
        s=row['metrics'];n=s['frequency'];population=row['population']
        row['deaths_per100_records']=s['mortality']/n*100 if s['mortality'] is not None else None
        row['injuries_per100_records']=s['injuries']/n*100 if s['injuries'] is not None else None
        row['registered_mortality_rate']=s['mortality']/population*100000 if s['mortality'] is not None and population else None
        row['mortality_ci95']=poisson_rate_interval(s['mortality'],population)
        row['population_rate_status']='Denominador Censo 2020; registro administrativo, no mortalidad vial completa.' if population else 'Sin denominador oficial del año; no extrapolado.'
    temporal_profiles=[{'municipality':m,'year':y,**temporal(group)} for (m,y),group in sorted(by_municipal_year.items())]
    by_year=defaultdict(list)
    for r in rows:by_year[r['date'][:4]].append(r)
    temporal_profiles.extend({'municipality':'Conjunto reportante','year':y,**temporal(group)} for y,group in sorted(by_year.items()))
    payload={'version':'0.2-intelligence','cutoff':cutoff,'generated_at':datetime.now(timezone.utc).isoformat(),
             'record_unit':'reported_crash_record','reference':reference,'zones':zones,'radar':radar,
             'radar_method':{'model':'Contraste binomial exacto condicional de dos conteos Poisson independientes, exposición=días.',
                             'fdr':'Benjamini-Hochberg sobre todas las zonas y cuatro ventanas, antes de filtrar.',
                             'gate':'Ambas ventanas: >=95% coordenadas conocidas por municipio; diferencia <=2.5 pp; baseline>=10 y total>=20. Sin ajuste ficticio por subregistro.',
                             'limits':'Comparabilidad proxy, no confirmación de exhaustividad. Independencia/Poisson pueden incumplirse. Alertas condicionales exploratorias, no vigilancia en tiempo real.'},
             'epidemiology':epidemiology,'temporal':[],'temporal_asset':'temporal.json',
             'method_availability':[{'method':'H3','status':'Exploratorio','reason':'Celdas R7, población fija; evita publicar posiciones individuales.'},
                                    {'method':'DBSCAN / HDBSCAN / KDE','status':'Investigación local','reason':'Comparación en UTM 14N bajo supuesto de grados WGS84; datum original no confirmado.'},
                                    {'method':'Moran I / Getis-Ord Gi*','status':'No calculado','reason':'Población truncada por frecuencia, sin malla completa/exposición ni pesos preespecificados. Inferencia sobre ranking seleccionado sería sesgada.'},
                                    {'method':'Intersecciones y segmentos','status':'No disponible','reason':'Red vial principal de contexto sin enlaces homologados con RATIV; no se inventan intersecciones o segmentos.'}],
             'limitations':['Resultados experimentales; registros no equivalen a eventos únicos garantizados.',
                            'Conteos clínicos agregados protegidos: nulos no se convierten en cero ni se recuperan con índices/ratios.',
                            'Población H3 seleccionada por frecuencia en 2024 y 2025; no representa todas las zonas ni permite inferir riesgo.',
                            'El IPIV requiere las cinco dimensiones, aunque un peso sea cero. Vulnerabilidad es evidencia documentada, no personas.',
                            'No hay edad/sexo exhaustivos ni denominadores válidos para AVPP/letalidad. Fallecidos registrados no equivalen a mortalidad a 30 días.']}
    dump(ROOT/'release/intelligence.json',payload)
    dump(ROOT/'release/temporal.json',{'profiles':temporal_profiles,'cutoff':cutoff,'note':'Día del evento × hora de reporte; sin imputación de periodos sin registros.'})
    dump(ROOT/'data/processed/intelligence_research.json',{'input_sha256':hashlib.sha256(records_path.read_bytes()).hexdigest(),'zones':research})
    print(json.dumps({'zones':len(zones),'ipiv_complete':reference['complete_cases'],'radar_tests':sum(r['q_value'] is not None for r in radar),'conditional_alerts':sum(r['statistical_alert'] for r in radar),'temporal_profiles':len(temporal_profiles)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--records',type=Path,required=True);args=parser.parse_args();build(args.records)
