from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).parent
def draw():
    r=json.loads((ROOT/'results/results.json').read_text());out=ROOT/'figures';out.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':230})
    labels=['Human','1 Survey','2 Reported\nattitudes','3 Generated\nattitudes','4 National','5 National\n+ attitudes','6 Local\nfast*','7 Local\nthinking*']
    fig,ax=plt.subplots(figsize=(7.3,3.2),layout='constrained')
    for j,(domain,label,color,marker) in enumerate([('visual','Visual and ecological','#444444','o'),('economic','Economic','#15707b','s'),('health','Environmental and health','#a66415','^')]):
        rows=[x for x in r['domain_summary'] if x['domain']==domain]
        x=np.arange(8)+(j-1)*.21;y=np.array([v['mean'] for v in rows]);err=np.array([[v['mean']-v['lo'] for v in rows],[v['hi']-v['mean'] for v in rows]])
        ax.errorbar(x,y,yerr=err,fmt=marker,color=color,capsize=2,label=label,ms=4,linewidth=1)
    ax.set(xticks=np.arange(8),xticklabels=labels,ylim=(1,5),ylabel='Mean importance (1 to 5)')
    ax.grid(axis='y',alpha=.18);ax.legend(loc='lower left',frameon=False,ncol=2,fontsize=8)
    ax.axvspan(5.55,7.45,color='#eeeeee',zorder=-1);ax.tick_params(axis='x',labelsize=8)
    fig.savefig(out/'domain_means.png');plt.close(fig)
    names={'energy_independence':'Energy independence','climate':'Climate change','wildlife':'Wildlife and ecosystems','reliability':'System reliability','economic':'Economic impacts','policy_process':'Policy process','health':'Health impacts','visual_land':'Visual and landscape','nuclear':'Nuclear energy'}
    fig,ax=plt.subplots(figsize=(7.2,3.4),layout='constrained');yy=np.arange(len(names))
    for j,(group,label,color,marker) in enumerate([('Human benchmark',f"Human ({r['response_audit'][0]['open_responses']} coded answers)",'#222222','o'),('Generated responses','Generated (12,791 responses)','#15707b','s')]):
        rows={x['theme']:x for x in r['theme_summary'] if x['sample']==group and x['dictionary']=='original'}
        vals=[100*rows[t]['share_responses'] for t in names]
        ax.scatter(vals,yy+(j-.5)*.2,label=label,color=color,marker=marker,s=24)
    ax.set(yticks=yy,yticklabels=list(names.values()),xlabel='Responses with each keyword theme (%)',xlim=(-1,60));ax.invert_yaxis();ax.grid(axis='x',alpha=.18);ax.legend(frameon=False,fontsize=8)
    fig.savefig(out/'themes.png');plt.close(fig)
if __name__=='__main__':draw()
