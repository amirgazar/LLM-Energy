"""Reproduce the ACIS 2026 study analysis from the supplied files, without network calls.

Only aggregate outputs are written. Source files are read without modification.
The human benchmark and primary summaries follow the original Data Analysis.R.
The profile workbook is not a substitute for the original human response source.
"""
from pathlib import Path
import argparse, hashlib, json, re
import numpy as np
import pandas as pd
from scipy import stats

LABELS = ['Not at all important', 'Slightly important', 'Moderately important', 'Important', 'Very important']
REFUSALS = ["Prefer not to answer", "I don't have enough information to answer", "I don't have enough information"]
DOMAINS = {'visual': list(range(1,5)), 'economic': list(range(5,9)), 'health': list(range(9,16))}
CONFIGS = {
    '1 Survey Demo': (1, 'Survey profiles'),
    '2 Survey Demo and Cov (human)': (2, 'Survey profiles and reported attitudes'),
    '2 Survey Demo and Cov (simulated)': (3, 'Survey profiles and generated attitudes'),
    '3 USA Demo': (4, 'National profiles'),
    '4 USA Demo and Cov (simulated)': (5, 'National profiles and generated attitudes'),
    '5 Local LLM (fast)': (6, 'Local fast model, archived'),
    '6 Local LLM (thinking)': (7, 'Local thinking model, archived'),
}
ORIGINAL = {
 'climate':['climate','emission','carbon','global warming'],
 'health':['health','asthma','respiratory','air pollution'],
 'economic':['cost','price','bill','jobs','employment','econom'],
 'visual_land':['visual','aesthetic','landscape','eyesore'],
 'wildlife':['wildlife','birds','bats','ecosystem'],
 'reliability':['reliab','baseload','intermitt','storage'],
 'nuclear':['nuclear','reactor'],
 'energy_independence':['independ','security','foreign'],
 'policy_process':['policy','government','leadership','planning'],
}
SENSITIVITY = {**ORIGINAL,
 'climate':ORIGINAL['climate']+['greenhouse'],
 'health':ORIGINAL['health']+['particulate'],
 'economic':ORIGINAL['economic']+['affordab'],
 'visual_land':ORIGINAL['visual_land']+['scenic','viewshed'],
 'wildlife':ORIGINAL['wildlife']+['habitat'],
 'reliability':ORIGINAL['reliability']+['blackout','grid stability'],
 'nuclear':['nuclear','reactor','fission','atomic','smr','small modular'],
 'energy_independence':['energy independ','energy security','energy sovereign','domestic energy','foreign oil','foreign energy','imported energy','self-sufficien','self sufficien'],
 'policy_process':ORIGINAL['policy_process']+['regulat','permitting'],
}
def clean_text(value):
    if pd.isna(value): return ''
    return re.sub(r'\s+', ' ', str(value)).strip().strip('"\'“”').strip()

def parse_rating(value):
    text='' if pd.isna(value) else str(value).strip()
    # Match the original R named-vector lookup exactly; do not unwrap quotes.
    for i,label in enumerate(LABELS,1):
        if text==label: return float(i),'valid'
    if clean_text(value).casefold() in [x.casefold() for x in REFUSALS]: return np.nan,'refusal'
    return np.nan,('missing' if not text else 'invalid')

def score_rows(d):
    d=d.copy(); codes=[]
    for i in range(1,16):
        col=f'Q{i}'
        if col not in d: raise ValueError(f'Missing required column: {col}')
        pairs=[parse_rating(x) for x in d[col]]
        d[f'score_{i}']=[x[0] for x in pairs]; codes.extend(x[1] for x in pairs)
    for name,items in DOMAINS.items(): d[name]=d[[f'score_{i}' for i in items]].mean(axis=1)
    d['health_visual']=d.health-d.visual
    d['economic_visual']=d.economic-d.visual
    d['health_economic']=d.health-d.economic
    return d,{s:codes.count(s) for s in ['valid','refusal','missing','invalid']}

def interval(values,level=.95):
    a=np.asarray(values,dtype=float);a=a[np.isfinite(a)];n=len(a)
    if n<2:return {'n':n,'mean':float(a[0]) if n else None,'se':None,'lo':None,'hi':None}
    mean=float(a.mean());se=float(a.std(ddof=1)/np.sqrt(n));half=float(stats.t.ppf((1+level)/2,n-1)*se)
    return dict(n=n,mean=mean,se=se,lo=mean-half,hi=mean+half)

def profile_values(d,cols):
    # Collapse repeated runs before calculating between-profile intervals.
    # These are descriptive intervals for the source profile pool, not public opinion.
    return d.groupby('profile_id',sort=True)[cols].mean()

def open_text(value):
    s=clean_text(value)
    return '' if s.lower() in ['', 'na','n/a','none','no','nothing','-'] else s

def code_themes(texts,book):
    return pd.DataFrame({k:[bool(re.search('|'.join(map(re.escape,v)),x.lower())) for x in texts] for k,v in book.items()})

def load_data(root):
    source=root/'1 Survey Results/1 Survey Results Analysis/all_responses_2024_06_25.csv'
    raw=pd.read_csv(source,low_memory=False)
    flags=[c for c in raw if c.strip()=='Believe valid']
    if len(flags)!=1:raise ValueError('Expected one screening flag column')
    selected=raw[raw[flags[0]].fillna('').str.startswith('Y')].copy()
    h=pd.DataFrame({'profile_id':selected.ResponseId.astype(str),'run':'Observed','config':0})
    for i in range(1,16):h[f'Q{i}']=selected[f'Q9_{i}']
    h['Q16']=selected['Q10'];h=h.reset_index(drop=True)
    if h.profile_id.duplicated().any():raise ValueError('Duplicate screened human IDs')
    datasets={0:h}; sources=[source];meta={0:{'name':'Human benchmark','q16_available':True}}
    for folder,(cid,name) in CONFIGS.items():
        files=sorted((root/'5 Final Results'/folder).glob('*/final_results.xlsx'))
        if not files:raise FileNotFoundError(folder)
        frames=[];q16=[]
        for file in files:
            d=pd.read_excel(file);q16.append('Q16' in d)
            d=d.rename(columns={'Respondent ID':'profile_id'})
            d['profile_id']=d.profile_id.astype(str);d['run']=file.parent.name;d['config']=cid
            if d.profile_id.duplicated().any():raise ValueError(f'Duplicate profile IDs within {file}')
            if 'Q16' not in d:d['Q16']=pd.NA
            frames.append(d);sources.append(file)
        datasets[cid]=pd.concat(frames,ignore_index=True)
        meta[cid]={'name':name,'q16_available':all(q16),'files':len(files)}
    return datasets,meta,sources

def analyse(root,out):
    out.mkdir(parents=True,exist_ok=True)
    datasets,meta,sources=load_data(root)
    means=[];contrasts=[];diagnostics=[];theme_rows=[];sensitivity=[];run_rows=[];item_rows=[]
    alltexts={'Human benchmark':[],'Generated responses':[]};scored={};profile_checks=[]
    columns=list(DOMAINS)+['health_visual','economic_visual','health_economic']
    for cid,d in datasets.items():
        scores,counts=score_rows(d);scored[cid]=scores;clusters=profile_values(scores,columns)
        texts=[x for x in map(open_text,d.Q16) if x]
        group='Human benchmark' if cid==0 else 'Generated responses'
        alltexts[group].extend(texts)
        diagnostics.append(dict(config=cid,name=meta[cid]['name'],rows=len(d),profiles=d.profile_id.nunique(),runs=d.run.nunique(),q16_available=meta[cid]['q16_available'],open_responses=len(texts),**counts))
        for domain in DOMAINS:
            z=interval(scores[domain]);legacy=z
            profile_checks.append(dict(config=cid,measure=domain,**interval(clusters[domain])))
            means.append(dict(config=cid,name=meta[cid]['name'],domain=domain,**z,pooled_mean=legacy['mean'],pooled_se=legacy['se'],valid_rows=legacy['n']))
        for contrast in ['health_visual','economic_visual','health_economic']:
            contrasts.append(dict(config=cid,name=meta[cid]['name'],contrast=contrast,**interval(scores[contrast])))
            profile_checks.append(dict(config=cid,measure=contrast,**interval(clusters[contrast])))
        for run,rd in scores.groupby('run'):
            for domain in DOMAINS:run_rows.append(dict(config=cid,run=run,domain=domain,**interval(rd[domain])))
        for i in range(1,16):
            values=scores[f'score_{i}'];valid=int(values.notna().sum())
            for rating in range(1,6):item_rows.append(dict(config=cid,item=i,rating=rating,count=int((values==rating).sum()),valid=valid,share=float((values==rating).sum()/valid) if valid else None))
        for label,book in [('original',ORIGINAL),('sensitivity',SENSITIVITY)]:
            coded=code_themes(texts,book);total=int(coded.sum().sum())
            for theme in book:
                count=int(coded[theme].sum())
                sensitivity.append(dict(config=cid,dictionary=label,theme=theme,count=count,open_responses=len(texts),share_responses=count/len(texts) if texts else None,theme_assignments=total,share_assignments=count/total if total else None))
    for group,texts in alltexts.items():
        for label,book in [('original',ORIGINAL),('sensitivity',SENSITIVITY)]:
            c=code_themes(texts,book);total=int(c.sum().sum())
            for k in book:
                count=int(c[k].sum())
                theme_rows.append(dict(sample=group,dictionary=label,theme=k,count=count,open_responses=len(texts),matched_responses=int(c.any(axis=1).sum()),theme_assignments=total,share_responses=count/len(texts) if texts else None,share_assignments=count/total if total else None))
    # Complete-item sensitivity uses only rows with all 15 ratings.
    complete=[]
    for cid,d in scored.items():
        good=d.dropna(subset=[f'score_{i}' for i in range(1,16)])
        c=good[columns]
        for col in columns:complete.append(dict(config=cid,measure=col,rows=len(good),**interval(c[col])))
    # Item distributions provide a check beyond the order of three means.
    items=pd.DataFrame(item_rows);tv=[]
    for cid in range(1,8):
        for item in range(1,16):
            h=items[(items.config==0)&(items.item==item)].sort_values('rating').share.to_numpy()
            s=items[(items.config==cid)&(items.item==item)].sort_values('rating').share.to_numpy()
            tv.append(dict(config=cid,item=item,total_variation=float(np.abs(h-s).sum()/2)))
    outputs={'domain_summary':means,'paired_contrasts':contrasts,'response_audit':diagnostics,'theme_summary':theme_rows,'theme_by_configuration':sensitivity,'run_summary':run_rows,'item_distribution':item_rows,'item_distance':tv,'complete_item_sensitivity':complete,'profile_sensitivity':profile_checks}
    for name,rows in outputs.items():pd.DataFrame(rows).to_csv(out/(name+'.csv'),index=False)
    manifest=[dict(path=str(f.relative_to(root)),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in sources]
    (out/'source_manifest.json').write_text(json.dumps(manifest,indent=2))
    (out/'results.json').write_text(json.dumps(outputs,indent=2,allow_nan=False))
    (out/'keyword_dictionary.json').write_text(json.dumps({'original':ORIGINAL,'sensitivity':SENSITIVITY},indent=2))
    print(pd.DataFrame(diagnostics).to_string(index=False))
    print(pd.DataFrame(contrasts).query("contrast == 'health_economic'").to_string(index=False))
    return outputs

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True,help='Original LLM-Energy folder, kept locally')
    p.add_argument('--output',type=Path,default=Path(__file__).parent/'results')
    a=p.parse_args();analyse(a.source.resolve(),a.output.resolve())
