"""Create one safe-to-edit scaffold; never overwrite an existing edition."""
import argparse,json
from datetime import datetime,timedelta
from build import ROOT,CATEGORIES,CATEGORY_NAMES,timestamp
p=argparse.ArgumentParser()
p.add_argument('--date',required=True)
p.add_argument('--cutoff',required=True)
a=p.parse_args()
date=datetime.strptime(a.date,'%Y-%m-%d').date()
cutoff=timestamp(a.cutoff)
target=ROOT/'_posts'/f'{a.date}-briefing.md'
if target.exists():
    raise SystemExit(f'Existing edition preserved; update this file in place: {target}')
state=json.loads((ROOT/'.ops/state.json').read_text(encoding='utf-8'))
start=timestamp(state['last_success_cutoff']) if state['last_success_cutoff'] else cutoff-timedelta(days=4)
meta={'title':'TODO: 회차 제목','publication_date':a.date,'published_at':cutoff.isoformat(timespec='seconds'),'research_cutoff':a.cutoff,'coverage_start':start.isoformat(timespec='seconds'),'primary_start':start.isoformat(timespec='seconds'),'coverage_start_label':start.strftime('%Y-%m-%d %H:%M'),'research_cutoff_label':cutoff.strftime('%Y-%m-%d %H:%M'),'coverage_note':'TODO: 대상 기간과 보충 여부','articles':[]}
body=[]
template=(ROOT/'templates/issue.md').read_text(encoding='utf-8')
for i,(cat,name) in enumerate(zip(CATEGORIES,CATEGORY_NAMES)):
    body.append(f'## {i+1}. {name} {{#{cat}}}\n')
    for j in range(3):
        issue=f'{cat}-TODO-{j+1}'
        meta['articles'].append({'id':issue,'event_key':issue,'title':'TODO','category':cat,'status':'새 이슈','event_date':None,'news_at':a.cutoff,'news_time_precision':'date','supplement':False,'sources':[],'image':None,'continuity_summary':'TODO'})
        body.append(template.replace('{{NUMBER}}',f'{i*3+j+1:02}').replace('{{ISSUE_ID}}',issue))
    body.append('> **논술 선생님 정리** TODO: 사실·해석·가치판단을 구분한 유용한 정리. 의미가 없으면 생략.\n')
target.parent.mkdir(exist_ok=True)
target.write_text('---\n'+json.dumps(meta,ensure_ascii=False,indent=2)+'\n---\n\n'+'\n'.join(body),encoding='utf-8',newline='\n')
print(target)
