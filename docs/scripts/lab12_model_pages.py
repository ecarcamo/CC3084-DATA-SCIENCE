from copy import deepcopy
import json
import zipfile
from pathlib import Path
from docs.scripts.build_lab12_report import ROOT, field, literal, color, projection, visual
from docs.scripts.lab12_final_pages import MODELS, PAGES, bookmark, slicer, date_slicer, measure_card, textbox

V6, V7, V8 = 'lab12_v6_predicciones', 'lab12_v7_errores', 'lab12_v8_diferencia'
SERIES, MULTI, SINGLE, DATES, METRIC = 'serie_modelos', 'modelos_v6', 'modelo_v8', 'fechas_modelos', 'metrica_v7'

def definitions(existing):
    result = deepcopy(existing)
    prefix = f'Report/definition/pages/{MODELS}'
    items = [deepcopy(value) for name, value in existing.items() if name.startswith(prefix+'/visuals/') and value['name'].startswith('nav_')]
    items += [slicer(SERIES, 'Serie · selección única', 'DimSerie', 'nombre', (24,112,320,96,0), ['Total']), slicer(MULTI, 'Modelos de V6 · selección múltiple', 'DimModelo', 'nombre', (360,112,496,96,1), ['SARIMA','Holt-Winters','Suavizamiento exponencial simple (SES)'],single=False)]
    dates=date_slicer();dates['name']=DATES;dates['position'].update(x=872,y=112,width=384);dates['visual']['visualContainerObjects']['title'][0]['properties']['text']=literal('Periodo de V6 y V8')
    def replace_dates(obj):
        if isinstance(obj,dict):
            for k,v in obj.items():
                if isinstance(v,str):obj[k]=v.replace('2010-01-01','2021-04-01')
                else:replace_dates(v)
        elif isinstance(obj,list):
            for v in obj:replace_dates(v)
    replace_dates(dates);items.append(dates)
    names=['Observado V6','Estimado SARIMA','Estimado Holt-Winters','Estimado SES','Estimado Seasonal Naive','Estimado Prophet']
    line=visual(V6,'lineChart','V6 · ¿Qué estimaron los modelos frente a lo registrado?',(24,264,1232,360,3),{'Category':[projection('Calendario','Date')],'Y':[projection('Medidas',n,'Measure',format='#,0') for n in names]})
    line['visual']['objects']={'categoryAxis':[{'properties':{'axisType':literal('Scalar'),'fontSize':literal(10)}}],'valueAxis':[{'properties':{'fontSize':literal(10)}}],'legend':[{'properties':{'show':literal(True),'fontSize':literal(10)}}],'dataPoint':[],'lineStyles':[]}
    for n,c,style in zip(names,['#1F4E79','#A65E16','#6B3A0C','#C46A12','#8A4B12','#D07A1E'],['solid','dashed','dotted','dashDot','dashed','dashDot']):
        selector={'metadata':'Medidas.'+n}
        line['visual']['objects']['dataPoint'].append({'selector':selector,'properties':{'fill':color(c)}})
        line['visual']['objects']['lineStyles'].append({'selector':selector,'properties':{'lineStyle':literal(style),'strokeWidth':literal(3 if n=='Observado V6' else 2),'showMarker':literal(n=='Observado V6')}})
    bars=visual(V7,'clusteredBarChart','V7 · ¿Qué modelo se equivoca menos?',(24,908,600,350,4),{'Category':[projection('DimModelo','nombre')],'Y':[projection('Medidas','Error modelo','Measure')],'Tooltips':[projection('DimSerie','nombre',nativeQueryRef='Serie')]})
    bars['visual']['query']['sortDefinition']={'sort':[{'field':field('Medidas','Error modelo','Measure'),'direction':'Ascending'}]}
    bars['visual']['objects']={'dataPoint':[{'properties':{'defaultColor':color('#A65E16')}}],'labels':[{'properties':{'show':literal(True),'labelDisplayUnits':literal(1),'fontSize':literal(10)}}],'valueAxis':[{'properties':{'start':literal(0)}}]}
    diff=visual(V8,'lineChart','V8 · Diferencia mensual: observado − estimado',(648,908,608,350,5),{'Category':[projection('Calendario','Date')],'Y':[projection('Medidas','Diferencia','Measure',format='#,0')]})
    diff['visual']['objects']={'dataPoint':[{'properties':{'defaultColor':color('#A65E16')}}],'categoryAxis':[{'properties':{'axisType':literal('Scalar')}}],'lineStyles':[{'properties':{'showMarker':literal(True),'strokeWidth':literal(2.5)}}],'y1AxisReferenceLine':[{'selector':{'id':'cero'},'properties':{'show':literal(True),'value':literal(0),'lineColor':color('#5B6B7A'),'style':literal('dashed'),'transparency':literal(0)}}]}
    diff['visual']['visualContainerObjects']['title'][0]['properties']['text']={'expr':field('Medidas','Titulo V8','Measure')}
    table=visual('tabla_metricas','tableEx','Métricas de los cinco modelos · 63 meses completos',(24,1390,1232,240,6),{'Values':[projection('DimModelo','nombre')]+[projection('Medidas',n+' modelo','Measure') for n in ['MAE','RMSE','MAPE']]})
    items += [line,bars,diff,table,slicer(METRIC,'Métrica de V7 · una unidad por eje','MetricaV7','Metrica',(24,754,600,96,7),['MAE']),slicer(SINGLE,'Modelo de V8 · selección única','DimModelo','nombre',(648,754,608,96,8),['SARIMA']),measure_card('mensaje_v6','Mensaje V6',(24,216,1232,44,9),True),measure_card('nota_v6','Nota V6',(24,632,1232,112,10)),measure_card('subtitulo_v7','Subtitulo V7',(24,856,600,48,11)),measure_card('mensaje_v7','Mensaje V7',(24,1264,600,64,12),True),measure_card('mensaje_v8','Mensaje V8',(648,1264,608,64,13),True),textbox('signo_v8','Positivo: el modelo estimó menos viajeros que los registrados. Negativo: estimó más. Cero: observado = estimado.',(648,1332,608,48,14),10),textbox('glosario_modelos','Estimado: cálculo para un mes ya registrado. MAE: distancia media en viajeros. RMSE: penaliza más los errores grandes. MAPE: error medio porcentual. Menor error histórico no garantiza precisión futura. Sin intervalos de confianza ni separación entrenamiento/evaluación documentada. Limpiar el selector de V6 muestra los cinco modelos.',(24,1640,1232,120,15),12)]
    for name,value in existing.items():
        if name.startswith(prefix+'/visuals/') and value['name'].startswith(('reset_','ayuda_')):
            item=deepcopy(value);item['position']['y']=1790;items.append(item)
    page=deepcopy(existing[prefix+'/page.json']);page['height']=1870
    data=[i['name'] for i in items if i['visual'].get('query')]
    v6targets=[V6,'nota_v6','mensaje_v6'];v7targets=[V7,'subtitulo_v7','mensaje_v7'];v8targets=[V8,'mensaje_v8']
    allowed={(SERIES,t) for t in v6targets+v7targets+v8targets+['tabla_metricas']}
    allowed|={(MULTI,t) for t in v6targets};allowed|={(DATES,t) for t in v6targets+v8targets};allowed|={(SINGLE,t) for t in v8targets};allowed|={(METRIC,t) for t in v7targets}
    page['visualInteractions']=[{'source':s,'target':t,'type':'DataFilter' if (s,t) in allowed else 'NoFilter'} for s in data for t in data if s!=t]
    for name in list(result):
        if name.startswith(prefix+'/visuals/'):del result[name]
    result[prefix+'/page.json']=page
    for item in items:result[prefix+'/visuals/'+item['name']+'/visual.json']=item
    result['Report/definition/bookmarks/inicial_'+MODELS+'.bookmark.json']=bookmark(MODELS,items)
    return result

def build(path):
    path=Path(path)
    with zipfile.ZipFile(path) as z:entries={n:z.read(n) for n in z.namelist()}
    old={n:json.loads(b) for n,b in entries.items() if n.startswith('Report/definition/') and n.endswith('.json')}
    new=definitions(old)
    for n in list(entries):
        if n.startswith('Report/definition/pages/'+MODELS+'/visuals/'):del entries[n]
    for n,obj in new.items():
        if n.startswith('Report/definition/pages/'+MODELS+'/') or n=='Report/definition/bookmarks/inicial_'+MODELS+'.bookmark.json':entries[n]=json.dumps(obj,ensure_ascii=False,indent=2).encode('utf-8')
    pages=json.loads(entries['Report/definition/pages/pages.json'])
    pages['activePageName']='lab12_inicio'
    entries['Report/definition/pages/pages.json']=json.dumps(pages,ensure_ascii=False,indent=2).encode('utf-8')
    entries.pop('SecurityBindings',None)
    from xml.etree import ElementTree
    ElementTree.register_namespace('', 'http://schemas.openxmlformats.org/package/2006/content-types')
    ct=ElementTree.fromstring(entries['[Content_Types].xml'])
    for child in list(ct):
        if child.get('PartName')=='/SecurityBindings':ct.remove(child)
    entries['[Content_Types].xml']=ElementTree.tostring(ct,encoding='utf-8',xml_declaration=True)
    temp=path.with_suffix('.tmp.pbix')
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in entries.items():z.writestr(n,b)
    with zipfile.ZipFile(temp) as z:
        assert z.testzip() is None
        assert z.read('DataModel')==entries['DataModel']
    temp.replace(path)

if __name__=='__main__':build(ROOT/'powerbi/observatorio_turismo.pbix')
