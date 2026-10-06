"""Controlled collection for a future rerun. Default: no network requests.

Use a new output directory for each set of settings. The archived study results
are never overwritten. Use only profiles cleared for the chosen service.
"""
from pathlib import Path
import argparse, hashlib, json, os, time, urllib.request, urllib.error
from analysis_REVISED import LABELS, REFUSALS, parse_rating

PROFILE_FIELDS=['State','Region','Division','Age','Gender','Education','Politics','Race','Income','Familiarity','Knowledge','Importance','Belief']
def final_answer(response,kind):
    choices=response.get('choices') or []
    if not choices:return None,'empty_response'
    choice=choices[0]
    if choice.get('finish_reason')!='stop':return None,'incomplete'
    # Never inspect reasoning or select a label mentioned inside an explanation.
    content=choice.get('message',{}).get('content')
    if not isinstance(content,str) or not content.strip():return None,'missing_final_answer'
    text=content.strip()
    if kind=='rating':
        _,status=parse_rating(text)
        return (text,status) if status in ['valid','refusal'] else (None,'invalid')
    return text,'valid'

def run(args):
    profiles=json.loads(args.profiles.read_text())
    questions=json.loads(args.questions.read_text())
    if not isinstance(profiles,list) or not profiles:raise ValueError('Profiles must be a non-empty JSON list')
    if len(questions)!=16:raise ValueError('Exactly 16 questions are required')
    if not args.endpoint.startswith('https://'):raise ValueError('Use an HTTPS endpoint')
    profile_ids=[str(p.get('profile_id','')) for p in profiles]
    if any(not p for p in profile_ids) or len(set(profile_ids))!=len(profile_ids):raise ValueError('Unique local profile_id values are required')
    settings={'model':args.model,'temperature':args.temperature,'rating_budget':args.rating_budget,'text_budget':args.text_budget,'endpoint':args.endpoint,'questions_sha256':hashlib.sha256(args.questions.read_bytes()).hexdigest()}
    print(json.dumps({'requests':len(profiles)*16,'execute':args.execute,'settings':settings},indent=2))
    if not args.execute:return
    key=os.environ.get('SURVEY_API_KEY')
    if not key:raise ValueError('Set SURVEY_API_KEY in the environment')
    args.output.mkdir(parents=True,exist_ok=True)
    settings_file=args.output/'settings_REVISED.json'
    if settings_file.exists() and json.loads(settings_file.read_text())!=settings:raise ValueError('Output directory has different settings')
    settings_file.write_text(json.dumps(settings,indent=2))
    for profile in profiles:
        sent_profile={k:profile[k] for k in PROFILE_FIELDS if k in profile}
        for q in questions:
            content='Answer this survey from the supplied profile.\nProfile: '+json.dumps(sent_profile,ensure_ascii=False)+'\n'+q['text']
            if q['kind']=='rating':content+='\nReturn exactly one option: '+json.dumps(LABELS+REFUSALS[:2])
            else:
                content+='\nThe previous rating items were:\n'+'\n'.join(x['text'] for x in questions if x['kind']=='rating')
                content+='\nIf you have no other concern, you may answer "None".'
            payload={'model':args.model,'temperature':args.temperature,'max_tokens':args.rating_budget if q['kind']=='rating' else args.text_budget,'messages':[{'role':'user','content':content}]}
            digest=hashlib.sha256(json.dumps([settings,profile['profile_id'],payload],sort_keys=True).encode()).hexdigest()
            target=args.output/(digest+'_REVISED.json')
            if target.exists():continue
            req=urllib.request.Request(args.endpoint,data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=120) as stream:response=json.load(stream)
            answer,status=final_answer(response,q['kind'])
            record={'profile_id':profile['profile_id'],'question_id':q['id'],'status':status,'answer':answer,'requested_model':args.model,'returned_model':response.get('model'),'response_id':response.get('id'),'finish_reason':(response.get('choices') or [{}])[0].get('finish_reason'),'usage':response.get('usage'),'prompt_sha256':hashlib.sha256(content.encode()).hexdigest(),'collected_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
            tmp=target.with_suffix('.REVISED.tmp');tmp.write_text(json.dumps(record,indent=2));tmp.replace(target)
            if status not in ['valid','refusal']:raise RuntimeError('Collection stopped after an incomplete or invalid answer. Inspect the record and use a new directory if settings change.')
            time.sleep(args.interval)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profiles',type=Path,required=True);p.add_argument('--questions',type=Path,default=Path(__file__).with_name('questions_REVISED.json'))
    p.add_argument('--endpoint',required=True,help='Full HTTPS chat-completions endpoint')
    p.add_argument('--model',required=True);p.add_argument('--temperature',type=float,default=.2)
    p.add_argument('--rating-budget',type=int,default=2048);p.add_argument('--text-budget',type=int,default=4096)
    p.add_argument('--interval',type=float,default=.2);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execute',action='store_true');a=p.parse_args()
    if min(a.rating_budget,a.text_budget)<1 or a.interval<0:p.error('Budgets must be positive and interval non-negative')
    run(a)
