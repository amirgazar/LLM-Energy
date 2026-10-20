"""Rebuild aggregate study analyses without altering historical inputs."""
import json,csv,math,re,statistics,ast,hashlib,itertools
from pathlib import Path
from collections import Counter,defaultdict
import argparse
parser=argparse.ArgumentParser(description="Reproduce the verified 161-profile analysis locally. No network requests or participant-level exports.")
parser.add_argument('--runs-root',type=Path,required=True)
parser.add_argument('--original-root',type=Path,required=True)
parser.add_argument('--benchmark',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
BASE=args.runs_root;ROOT=args.original_root;OUT=args.output;OUT.mkdir(parents=True,exist_ok=True)
def beta_cf(a, b, x):
    qab = a + b
    qap = a + 1
    qam = a - 1
    c = 1.0
    d = 1 - qab * x / qap
    d = 1 / (d if abs(d) > 1e-300 else 1e-300)
    h = d
    for m in range(1, 301):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        d = d if abs(d) > 1e-300 else 1e-300
        c = 1 + aa / c
        c = c if abs(c) > 1e-300 else 1e-300
        d = 1 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        d = d if abs(d) > 1e-300 else 1e-300
        c = 1 + aa / c
        c = c if abs(c) > 1e-300 else 1e-300
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 3e-14:
            break
    return h

def ibeta(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x))
    return bt * beta_cf(a, b, x) / a if x < (a + 1) / (a + b + 2) else 1 - bt * beta_cf(b, a, 1 - x) / b

def tcdf(t, df):
    z = ibeta(df / 2, 0.5, df / (df + t * t))
    return 1 - z / 2 if t >= 0 else z / 2

def tcrit(df):
    lo, hi = (0.0, 100.0)
    for _ in range(70):
        mid = (lo + hi) / 2
        if tcdf(mid, df) < 0.975:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

def describe(v):
    v = [x for x in v if x is not None]
    n = len(v)
    mean = statistics.mean(v) if n else None
    se = statistics.stdev(v) / math.sqrt(n) if n > 1 else None
    c = tcrit(n - 1) * se if n > 1 else None
    return {'n': n, 'mean': mean, 'standard_error': se, 'ci95_low': mean - c if c is not None else None, 'ci95_high': mean + c if c is not None else None}
ns={'tcdf':tcdf,'ibeta':ibeta};assert abs(tcrit(30)-2.042272456)<1e-6
DOM={'Visual and ecological':list(range(1,5)),'Economic':list(range(5,9)),'Environmental health':list(range(9,16))};PAIRS=[('Environmental health','Visual and ecological'),('Economic','Visual and ecological'),('Environmental health','Economic')]
SCORE={v:i for i,v in enumerate(['Not at all important','Slightly important','Moderately important','Important','Very important'],1)}
def avg(x):
 x=[v for v in x if v is not None];return statistics.mean(x) if x else None
def numeric(x):return SCORE.get(x)
def ds(r,complete=False):
 if complete and any(numeric(r.get(f'Q{q}')) is None for q in range(1,16)):return {d:None for d in DOM}
 return {d:avg([numeric(r.get(f'Q{q}')) for q in qs]) for d,qs in DOM.items()}
def stats(x):
 v=[z for z in x if z is not None];s=describe(v);se=s['standard_error'];m=s['mean'];s['t_statistic']=m/se if se else None;s['p_two_sided']=2*(1-ns['tcdf'](abs(m/se),len(v)-1)) if se else (0. if m else None);return s
def write(name,rows):
 with (OUT/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else []);w.writeheader();w.writerows(rows)
def load(p):return json.loads(p.read_text())

def collect():
 data={};checks=[];paths=[];bench=args.benchmark;human=load(bench);paths.append(bench);assert len(human)==161
 data['Human benchmark']=[[r] for r in human]
 for tag,label in [('demo','1 GPT demographic'),('human','2 GPT demographic and reported attitudes'),('simulated','3 GPT demographic and generated attitudes')]:
  groups=[];missing=0
  for pi in range(1,162):
   runs=[]
   for rep in range(1,4):
    p=BASE/'Verified 161 OpenAI Rerun 2026-10-18'/tag/f'run_{rep}'/f'p{pi:03}'/'result.json'
    if not p.exists():missing+=1;continue
    r=load(p);assert r['profile_index']==pi and all(f'Q{q}' in r for q in range(1,17));runs.append(r);paths.append(p)
   groups.append(runs)
  checks.append({'dataset':label,'expected_profile_runs':483,'missing_profile_runs':missing});data[label]=groups
 for folder,label in [('3 USA Demo','4 NPORS demographic'),('4 USA Demo and Cov (simulated)','5 NPORS demographic and generated attitudes')]:
  p=ROOT/'5 Final Results'/folder/'Simulation 1/final_results.json';r=load(p);r=list(r.values()) if isinstance(r,dict) else r;assert len(r)==5626;data[label]=[[x] for x in r];paths.append(p)
 for folder,label in [('Verified 161 Rerun 2026-10-18','6 Locally deployed gpt-oss-120b'),('Verified 161 DeepSeek Low Replacement 2026-10-19','7 Locally deployed DeepSeek-V4.1-Flash lower reasoning')]:
  groups=[];missing=0
  for pi in range(1,162):
   row={'profile_index':pi}
   for q in range(1,17):
    p=BASE/folder/'responses'/f'p{pi:03}_q{q:02}.json'
    if not p.exists() or load(p)['status']!='complete':missing+=1;continue
    row[f'Q{q}']=load(p)['answer'];paths.append(p)
   groups.append([row])
  checks.append({'dataset':label,'expected_profile_runs':2576,'missing_profile_runs':missing});data[label]=groups
 write('completion_checks.csv',checks)
 if any(x['missing_profile_runs'] for x in checks):
  print(json.dumps({'status':'awaiting_complete_runs','checks':checks}));return None
 # Normalize formatting around exact rating labels only; leave source files and written answers unchanged.
 allowed=set(SCORE)|{"I don't have enough information to answer", "Prefer not to answer"}
 for groups in data.values():
  for runs in groups:
   for row in runs:
    for q in range(1,16):
     key=f'Q{q}'; value=row.get(key)
     if isinstance(value,str):
      cleaned=value.strip().strip('"').strip()
      if cleaned in allowed:row[key]=cleaned
 return data

def main():
 data=collect()
 if data is None:return False
 domains=[];contrasts=[];profile_domains={};perrun=[];refusals=[];anova=[];profile_rows=[];profile_contrasts=[]
 for complete in [False,True]:
  mode='complete_15_items' if complete else 'available_items'
  for label,groups in data.items():
   profiles=[{d:avg([ds(r,complete)[d] for r in runs]) for d in DOM} for runs in groups]
   if not complete:profile_domains[label]=profiles
   for pi,p in enumerate(profiles,1):profile_rows.append({'dataset':label,'analysis':mode,'profile_index':pi,**p})
   for d in DOM:domains.append({'dataset':label,'analysis':mode,'domain':d,**describe([p[d] for p in profiles])})
   for a,b in PAIRS:
    diffs=[avg([ds(r,complete)[a]-ds(r,complete)[b] for r in runs if ds(r,complete)[a] is not None and ds(r,complete)[b] is not None]) for runs in groups]
    contrasts.append({'dataset':label,'analysis':mode,'difference':a+' minus '+b,**stats(diffs)})
    for pi,v in enumerate(diffs,1):profile_contrasts.append({'dataset':label,'analysis':mode,'profile_index':pi,'difference':a+' minus '+b,'value':v})
   vals=[[p[d] for d in DOM] for p in profiles if all(p[d] is not None for d in DOM)];n=len(vals)
   if n>1:
    grand=statistics.mean(v for row in vals for v in row);cols=[statistics.mean(row[j] for row in vals) for j in range(3)];rm=[statistics.mean(row) for row in vals];ssdomain=n*sum((x-grand)**2 for x in cols);sserror=sum((vals[i][j]-rm[i]-cols[j]+grand)**2 for i in range(n) for j in range(3));f=(ssdomain/2)/(sserror/(2*(n-1))) if sserror>0 else None;p=1-ns['ibeta'](1,n-1,2*f/(2*f+2*(n-1))) if f is not None else None;anova.append({'dataset':label,'analysis':mode,'n_profiles':n,'F':f,'df1':2,'df2':2*(n-1),'p_unadjusted_sphericity_assumed':p})
 write('domain_scores.csv',domains);write('within_profile_differences.csv',contrasts);write('repeated_measures_anova.csv',anova)
 # Explicit paired differences against the same human profile, only for matched datasets.
 paired=[];alignment=[]
 h=profile_domains['Human benchmark'];hm={d:avg([p[d] for p in h]) for d in DOM}
 for label,profiles in profile_domains.items():
  means={d:avg([p[d] for p in profiles]) for d in DOM};is_matched=label.startswith(('1 ','2 ','3 ','6 ','7 '))
  alignment.append({'dataset':label,'profile_count':len(profiles),'matched_to_human':is_matched,'all_domain_means_within_0_5':all(abs(means[d]-hm[d])<=.5 for d in DOM) if is_matched else None,'health_above_visual':means['Environmental health']>means['Visual and ecological'],'economic_above_visual':means['Economic']>means['Visual and ecological']})
  if is_matched:
   for d in DOM:
    dif=[p[d]-b[d] for p,b in zip(profiles,h) if p[d] is not None and b[d] is not None];paired.append({'dataset':label,'domain':d,'comparison':'generated minus same human respondent',**stats(dif),'mean_absolute_difference':avg([abs(v) for v in dif])})
 write('matched_model_human_differences.csv',paired);write('concordance.csv',alignment)
 # Preserve equal profile weight for response shares, averaging repetitions first.
 distributions=[];tvd=[]
 def shares(groups,q,allcategories=False):
  cats=list(SCORE)+['Refusal','Blank'] if allcategories else list(SCORE);vec=[]
  for runs in groups:
   answers=[r.get(f'Q{q}') for r in runs];mapped=[a if a in SCORE else 'Blank' if a is None or str(a).strip() in ['', 'NA','None','nan'] else 'Refusal' for a in answers]
   if not allcategories:mapped=[a for a in mapped if a in SCORE]
   if mapped:vec.append([mapped.count(c)/len(mapped) for c in cats])
  return cats,[statistics.mean(v[j] for v in vec) for j in range(len(cats))],len(vec)
 for label,groups in data.items():
  rows=[r for g in groups for r in g];counts=Counter(r.get(f'Q{q}') for r in rows for q in range(1,16));refusals.append({'dataset':label,'profiles':len(groups),'response_rows':len(rows),'rating_slots':len(rows)*15,'numeric_answers':sum(n for k,n in counts.items() if k in SCORE),'refusals':sum(n for k,n in counts.items() if k not in SCORE and k is not None and str(k).strip() not in ['', 'NA','None','nan']),'blanks':sum(n for k,n in counts.items() if k is None or str(k).strip() in ['', 'NA','None','nan'])})
  for q in range(1,16):
   for allcats in [False,True]:
    cats,ss,n=shares(groups,q,allcats);_,hh,_=shares(data['Human benchmark'],q,allcats)
    for c,v in zip(cats,ss):distributions.append({'dataset':label,'question':q,'denominator':'all answers' if allcats else 'numeric only','category':c,'share_equal_profile_weight':v,'profiles_with_answers':n})
    if label!='Human benchmark':tvd.append({'dataset':label,'question':q,'denominator':'all answers' if allcats else 'numeric only','total_variation':sum(abs(x-y) for x,y in zip(ss,hh))/2})
  for rep in range(max(len(g) for g in groups)):
   rs=[g[rep] for g in groups if len(g)>rep]
   for d in DOM:perrun.append({'dataset':label,'run':rep+1,'domain':d,**describe([ds(r)[d] for r in rs])})
 write('refusals_and_blanks.csv',refusals);write('item_response_shares.csv',distributions);write('item_total_variation.csv',tvd);write('per_run_domain_scores.csv',perrun)
 books=json.loads((Path(__file__).parent/'verified_keywords.json').read_text())
 def clean(t):
  s=' '.join(str(t or '').split());return s if s.lower() not in ['', 'na','n/a','none','no','nothing','-','nan'] else ''
 themes=[];cooccur=[];written=[];textsets={label:groups for label,groups in data.items()}
 textsets['Pooled five commercial configurations']=[g for label,groups in data.items() if label.startswith(('1 ','2 ','3 ','4 ','5 ')) for g in groups]
 textsets['Pooled two locally deployed configurations']=[g for label,groups in data.items() if label.startswith(('6 ','7 ')) for g in groups]
 for label,groups in textsets.items():
  texts=[clean(r.get('Q16')) for g in groups for r in g];nonblank=[t for t in texts if t];lengths=[len(t.split()) for t in nonblank]
  written.append({'dataset':label,'profile_count':len(groups),'response_rows':len(texts),'usable_written_answers':len(nonblank),'median_words':statistics.median(lengths) if lengths else None,'minimum_words':min(lengths) if lengths else None,'maximum_words':max(lengths) if lengths else None})
  for book,words in books.items():
   flags=[{k:any(w in t.lower() for w in ws) for k,ws in words.items()} for t in nonblank];counts={k:sum(r[k] for r in flags) for k in words};total=sum(counts.values());matched=sum(any(r.values()) for r in flags)
   for theme,n in counts.items():
    pv=[]
    for g in groups:
     tt=[clean(r.get('Q16')) for r in g];tt=[t for t in tt if t]
     if tt:pv.append(statistics.mean(any(w in t.lower() for w in words[theme]) for t in tt))
    themes.append({'dataset':label,'dictionary':book,'theme':theme,'responses_with_theme':n,'usable_responses':len(nonblank),'responses_with_any_theme':matched,'total_theme_mentions':total,'percent_of_responses':100*n/len(nonblank) if nonblank else None,'percent_of_mentions':100*n/total if total else None,'percent_equal_profile_weight':100*statistics.mean(pv) if pv else None})
   for a,b in itertools.combinations(words,2):cooccur.append({'dataset':label,'dictionary':book,'theme_a':a,'theme_b':b,'responses_with_both':sum(r[a] and r[b] for r in flags),'usable_responses':len(nonblank)})
 write('written_response_counts.csv',written);write('written_themes_both_dictionaries.csv',themes);write('theme_cooccurrence.csv',cooccur)
 # Source profile counts, not repeated rows, define uncertainty estimates.
 summary={'status':'complete','verified_human_profiles':161,'new_model_profiles_per_configuration':161,'total_generated_response_rows':sum(len(g) for label,groups in data.items() if label!='Human benchmark' for g in groups),'commercial_repeats':3,'local_repeats':1,'npors_profiles_per_configuration':5626,'npors_status':'Existing results retained; separate population, not matched to human respondents','mean_numeric_item_tvd':{label:statistics.mean(r['total_variation'] for r in tvd if r['dataset']==label and r['denominator']=='numeric only') for label in data if label!='Human benchmark'},'limitations':['Intervals describe these profiles, not a representative population.','DeepSeek is an alternative to Kimi; differences do not isolate reasoning effects.','Commercial and local prompts and temperatures differ, as recorded.','Age is unreported for 25 profiles.','No exact historical replication: current service models may differ.','NPORS results were generated earlier and use a different population.','Keyword counts do not establish semantic agreement.','Local models have one run per profile; repeat variability is not measured.','ANOVA is unadjusted and assumes sphericity; paired contrasts are the primary results.']}
 (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
 lines=['CORRECTED 161-PROFILE ANALYSIS','Prepared for Amir Gazar','', 'All requested model runs passed the completion checks.','Commercial configurations: three runs per profile, averaged within each profile before calculating intervals.','Locally deployed models: one run per profile. The verified human benchmark contains 161 respondents.','', 'Domain means and 95% intervals']
 for r in domains:
  if r['analysis']=='available_items':lines.append(f"{r['dataset']} | {r['domain']}: {r['mean']:.3f} [{r['ci95_low']:.3f}, {r['ci95_high']:.3f}], n={r['n']}")
 lines+=['','Individual-question differences from human answer shares (0 identical, 1 no overlap)']+[f'{k}: {v:.3f}' for k,v in summary['mean_numeric_item_tvd'].items()]
 lines+=['','Limits']+summary['limitations']
 (OUT/'Analysis Findings REVISED.txt').write_text('\n'.join(lines)+'\n')
 print('Analysis complete:',OUT);return True
if __name__=='__main__':main()
