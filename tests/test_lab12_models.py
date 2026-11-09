import json
import zipfile
from pathlib import Path
from docs.scripts.build_lab12_report import ROOT, field
from docs.scripts.lab12_model_pages import definitions, MODELS, V6, V7, V8, MULTI, SINGLE, SERIES, DATES, METRIC

def report():
    with zipfile.ZipFile(ROOT/'powerbi/observatorio_turismo.pbix') as z:
        return {n:json.loads(z.read(n)) for n in z.namelist() if n.startswith('Report/definition/') and n.endswith('.json')}

def test_models_controls_do_not_change_unrelated_charts():
    p=report()[f'Report/definition/pages/{MODELS}/page.json']
    interactions={(i['source'],i['target']):i['type'] for i in p['visualInteractions']}
    assert interactions[MULTI,V6]=='DataFilter'
    assert interactions[MULTI,V7]==interactions[MULTI,V8]=='NoFilter'
    assert interactions[SINGLE,V8]=='DataFilter'
    assert interactions[SINGLE,V6]==interactions[SINGLE,V7]=='NoFilter'
    assert interactions[DATES,V6]==interactions[DATES,V8]=='DataFilter'
    assert interactions[DATES,V7]=='NoFilter'
    assert interactions[METRIC,V7]=='DataFilter'
    assert interactions[V7,V6]==interactions[V7,V8]=='NoFilter'

def test_models_measures_preserve_units_and_selections():
    m=json.loads((ROOT/'powerbi/medidas_diego.json').read_text(encoding='utf-8'))
    assert 'KEEPFILTERS' in m['Estimado SES']['expression']
    assert 'REMOVEFILTERS ( DimSerie )' in m['Error modelo']['expression']
    assert '\\%' in m['Error modelo']['formatStringExpression']
    assert m['Error modelo']['formatString']==''
    assert 'CALCULATE ( MIN ( DimModelo[orden] ) )' in m['Nota V6']['expression']

def test_models_initial_state_contains_three_models_and_independent_model():
    f=report();prefix=f'Report/definition/pages/{MODELS}/visuals/'
    multi=f[prefix+MULTI+'/visual.json']['visual']['objects']['general'][0]['properties']['filter']['filter']
    assert len(multi['Where'][0]['Condition']['In']['Values'])==3
    book=f['Report/definition/bookmarks/inicial_'+MODELS+'.bookmark.json']
    states=book['explorationState']['sections'][MODELS]['visualContainers']
    for n in [MULTI,SINGLE,SERIES,DATES,METRIC]:assert n in states
    line=f[prefix+V6+'/visual.json']['visual']
    assert len(line['query']['queryState']['Y']['projections'])==6

def test_models_patch_preserves_other_pages():
    source=report();out=definitions(source)
    for n,v in source.items():
        if n.startswith('Report/definition/pages/') and not n.startswith('Report/definition/pages/'+MODELS+'/'):assert out[n]==v


def test_v7_aliases_are_unique_for_native_query():
    f=definitions(report());q=f[f"Report/definition/pages/{MODELS}/visuals/{V7}/visual.json"]["visual"]["query"]["queryState"]
    aliases=[p["nativeQueryRef"] for role in q.values() for p in role["projections"]]
    assert len(aliases)==len(set(aliases))
