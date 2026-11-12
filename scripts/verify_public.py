"""Verify the deployed bytes before advancing the successful research cutoff."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from build import ROOT, CONFIG, KST, BASE, read_post, validate, issue_path

def get(path):
    url=CONFIG['url']+BASE+'/'+path.lstrip('/')
    request=Request(url,headers={'User-Agent':'LearningNewsArchive/1.0', 'Cache-Control':'no-cache'})
    with urlopen(request,timeout=45) as response:
        assert response.status==200, f'HTTP {response.status}: {url}'
        return response.read()

def verify(date,mark=False):
    post=read_post(ROOT/'_posts'/f'{date}-briefing.md')
    validate(post)
    manifest=json.loads(get('publication-manifest.json'))
    item=next(x for x in manifest['issues'] if x['date']==date)
    digest=hashlib.sha256(post['_path'].read_bytes()).hexdigest()
    assert item['source_sha256']==digest,'공개된 회차가 현재 원본과 다름'
    assert hashlib.sha256(get(f'markdown/{date}-briefing.md')).hexdigest()==digest,'공개 Markdown 원본 불일치'
    page=get(issue_path(post)).decode('utf-8')
    assert '<html lang="ko">' in page
    for article in post['articles']:
        assert f'id="{article["id"]}"' in page,'공개 기사 앵커 누락'
        for source in article['sources']:
            from html import escape
            assert escape(source['url'],quote=True) in page,'공개 출처 링크 누락'
    for c in ['world','korea','culture','technology','science']:
        assert f'href="#{c}"' in page,'공개 목차 누락'
    for path in ['', 'archive/',f'archive/{date[:4]}/',f'archive/{date[:4]}/{date[5:7]}/']:
        content=get(path).decode('utf-8')
        assert BASE+'/'+issue_path(post) in content, f'공개 목록 반영 안 됨: {path}'
    assert len(get('assets/style.css'))>1000,'스타일 로딩 실패'
    for image in item['images']:
        blob=get(image)
        assert len(blob)>100, '공개 이미지가 비어 있음'
        assert blob.startswith((b'\x89PNG', b'\xff\xd8\xff', b'GIF8', b'RIFF')), '이미지 응답이 아님'
        assert BASE+'/'+image in page,'이미지가 본문에 없음'
    checked=datetime.now(KST).isoformat(timespec='seconds')
    report={'date':date,'url':item['url'],'research_cutoff':post['research_cutoff'],'verified_at':checked,'source_sha256':digest,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'checks':['source_hash','public_markdown_hash','15_articles','5_categories','source_links_in_html','home','archive','year_archive','month_archive','stylesheet','available_images'],'image_count':len(item['images'])}
    if mark:
        state_path=ROOT/'.ops/state.json'
        previous=json.loads(state_path.read_text(encoding='utf-8'))
        if previous['last_success_cutoff']:
            assert datetime.fromisoformat(post['research_cutoff']) >= datetime.fromisoformat(previous['last_success_cutoff']), '과거 회차 수정은 성공 기준 시각을 되돌릴 수 없음'
        state={'last_success_cutoff':post['research_cutoff'],'last_success_issue':date,'last_success_url':item['url'],'last_verified_at':checked}
        recent_path=ROOT/'.ops/recent-issues.json'
        recent=json.loads(recent_path.read_text(encoding='utf-8'))
        current_ids={a['id'] for a in post['articles']}
        entries=[{'id':a['id'],'title':a['title'],'change':a['continuity_summary'],'link':item['url']+'#'+a['id']} for a in post['articles']]
        entries += [a for a in recent['issues'] if a['id'] not in current_ids]
        recent={'last_success_cutoff':post['research_cutoff'],'issues':entries[:30]}
        for path,data in [(recent_path,recent),(state_path,state),(ROOT/'.ops/runs'/f'{date}.json',report)]:
            path.parent.mkdir(parents=True,exist_ok=True)
            temporary=path.with_suffix('.tmp')
            temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            temporary.replace(path)
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--date',required=True)
    parser.add_argument('--mark-success',action='store_true')
    args=parser.parse_args()
    verify(args.date,args.mark_success)
