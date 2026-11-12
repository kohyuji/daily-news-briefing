"""Build only public, prewritten content. No network or AI calls."""
from __future__ import annotations
import hashlib
import html
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.vendor'))
import markdown

KST = timezone(timedelta(hours=9))
CATEGORIES = ['world', 'korea', 'culture', 'technology', 'science']
CATEGORY_NAMES = ['세계정세·외교·국제정치', '한국의 정치·경제·사회', '문화예술·콘텐츠 산업', '과학기술', '자연과학·기초과학']
CONFIG = json.loads((ROOT / 'site.json').read_text(encoding='utf-8'))
BASE = CONFIG['baseurl'].rstrip('/')
OUT = ROOT / '_site'

def timestamp(value):
    result = datetime.fromisoformat(value)
    if result.utcoffset() != timedelta(hours=9):
        raise ValueError(f'한국시간 +09:00 필요: {value}')
    return result

def read_post(path):
    raw = path.read_text(encoding='utf-8')
    if not raw.startswith('---\n'):
        raise ValueError(f'{path.name}: JSON front matter 필요')
    front, body = raw[4:].split('\n---\n', 1)
    meta = json.loads(front)  # JSON is a deliberately limited, valid YAML subset.
    meta['_body'] = body
    meta['_path'] = path
    return meta

def validate(p):
    date = p['publication_date']
    datetime.strptime(date, '%Y-%m-%d')
    assert p['_path'].name == f'{date}-briefing.md', '날짜별 문서 이름 불일치'
    assert timestamp(p['published_at']).date().isoformat() == date
    cutoff = timestamp(p['research_cutoff'])
    start = timestamp(p['coverage_start'])
    primary = timestamp(p['primary_start'])
    assert start <= primary < cutoff, '대상 기간 오류'
    assert start >= cutoff - timedelta(days=7), '7일 초과 보충 금지'
    articles = p['articles']
    assert len(articles) == 15, '기사 15개 필요'
    assert Counter(a['category'] for a in articles) == Counter({c:3 for c in CATEGORIES}), '분야별 3개 필요'
    assert len({a['id'] for a in articles}) == 15, '중복 이슈 식별자'
    assert len({a['event_key'] for a in articles}) == 15, '중복 사건'
    assert len(re.findall(r'^### ', p['_body'], re.M)) == 15, '본문 기사 수 오류'
    assert '\ue200' not in p['_body'] and 'turn0search' not in p['_body'], '채팅 전용 인용 금지'
    sections = re.findall(r'^## .+?\{#(world|korea|culture|technology|science)\}\s*$', p['_body'], re.M)
    assert sections == CATEGORIES, '5개 분야 목차 순서 오류'
    for a in articles:
        assert re.fullmatch(r'[a-z0-9-]+', a['id']), '잘못된 이슈 ID'
        marker = '{#' + a['id'] + '}'
        assert p['_body'].count(marker) == 1, f"본문 ID 누락: {a['id']}"
        after = p['_body'].split(marker, 1)[1]
        segment = re.split(r'^##?\s|^###\s', after, 1, flags=re.M)[0]
        assert len(segment) >= 800, f"설명 깊이 확인 필요: {a['id']}"
        assert a['status'] in ['새 이슈', '계속되는 이슈', '상황 변화']
        assert len(a['sources']) >= 2, f"출처 2개 필요: {a['id']}"
        assert len({s['url'] for s in a['sources']}) == len(a['sources'])
        for s in a['sources']:
            assert s['url'].startswith('https://') and s['title'] and s['publisher']
            assert s['url'] in segment, f"출처 본문 링크 누락: {a['id']}"
            if s['published_date'] is not None:
                datetime.strptime(s['published_date'], '%Y-%m-%d')
            assert s['verification'] == 'original_read', '검색 요약만으로 작성 금지'
        news_time = timestamp(a['news_at'])
        assert start <= news_time <= cutoff, '대상 기간 밖 기사'
        assert a['supplement'] == (news_time < primary), '보충 표시 오류'
        if a['supplement']:
            assert '7일 이내 보충' in segment
        if a.get('event_date'):
            datetime.strptime(a['event_date'], '%Y-%m-%d')
        image = a.get('image')
        if image:
            expected = f"assets/images/{date[:4]}/{date[5:7]}/{date}/"
            assert image['path'].startswith(expected)
            assert image['license'] and image['license_url'] and image['source_url']
            assert (ROOT / image['path']).is_file()
            assert image['path'] in segment
        else:
            assert '관련 이미지 미확보' in segment, '이미지 미확보 표시 필요'

def e(value):
    return html.escape(str(value), quote=True)

def href(path):
    return BASE + '/' + path.lstrip('/')

def issue_path(p):
    d = p['publication_date']
    return f'briefings/{d[:4]}/{d[5:7]}/{d}/'

def write_page(path, title, content, description='배경과 맥락으로 배우는 한국어 뉴스 브리핑'):
    target = OUT / path / 'index.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    template = Template((ROOT / 'templates/base.html').read_text(encoding='utf-8'))
    target.write_text(template.substitute(title=e(title), content=content, description=e(description), base=BASE, canonical=e(CONFIG['url'] + href(path) + ('/' if path and not path.endswith('/') else ''))), encoding='utf-8')

def edition_list(posts):
    items = []
    for p in posts:
        items.append(f'<li><time datetime="{e(p["published_at"])}">{e(p["publication_date"])} 발행</time><a href="{href(issue_path(p))}">{e(p["title"])}</a><p>뉴스 대상: {e(p["coverage_start_label"])} ~ {e(p["research_cutoff_label"])}</p></li>')
    return '<ul class="edition-list">' + ''.join(items) + '</ul>'

def build():
    posts = sorted([read_post(x) for x in (ROOT / '_posts').glob('*-briefing.md')], key=lambda p:p['publication_date'], reverse=True)
    for p in posts:
        validate(p)
    assert len({p['publication_date'] for p in posts}) == len(posts), '같은 날짜 중복 회차'
    # Only remove our known build output, never arbitrary input paths.
    assert OUT.resolve() == ROOT.resolve() / '_site'
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / 'assets', OUT / 'assets')
    (OUT / '.nojekyll').write_text('', encoding='utf-8')
    by_year = defaultdict(list)
    by_month = defaultdict(list)
    manifest = {'schema_version':1, 'timezone':'Asia/Seoul', 'issues':[]}
    for p in posts:
        d = p['publication_date']
        by_year[d[:4]].append(p)
        by_month[d[:7]].append(p)
        body = p['_body'].replace('{{BASE}}', BASE)
        rendered = markdown.markdown(body, extensions=['extra', 'sane_lists'])
        raw_path = f'markdown/{d}-briefing.md'
        raw_target = OUT / raw_path
        raw_target.parent.mkdir(exist_ok=True)
        raw_target.write_bytes(p['_path'].read_bytes())
        toc = '<nav class="toc" aria-label="5개 분야 목차"><div><strong>이번 회차의 다섯 분야</strong><ol>' + ''.join(f'<li><a href="#{c}">{n}</a></li>' for c,n in zip(CATEGORIES,CATEGORY_NAMES)) + '</ol></div></nav>'
        content = f'<article class="issue"><div class="breadcrumbs"><a href="{href("archive/")}">아카이브</a> / <a href="{href("archive/"+d[:4]+"/")}">{d[:4]}년</a> / <a href="{href("archive/"+d[:4]+"/"+d[5:7]+"/")}">{int(d[5:7])}월</a></div><header class="hero"><div class="eyebrow">LEARNING BRIEF · {d}</div><h1>{e(p["title"])}</h1><div class="meta"><p>발행일: {d} · 5개 분야, 15개 기사</p><p>뉴스 대상 기간: {e(p["coverage_start_label"])} ~ {e(p["research_cutoff_label"])} (KST)</p><p>조사 기준 시각: {e(p["research_cutoff_label"])} (KST)</p><p>{e(p["coverage_note"])}</p></div></header>{toc}<div class="reading-tools"><a href="{href(raw_path)}" download>Markdown 원본 내려받기</a><a href="{href("archive/"+d[:4]+"/"+d[5:7]+"/")}">이번 달 발행 목록</a></div><div class="prose">{rendered}</div></article>'
        write_page(issue_path(p), p['title'], content)
        manifest['issues'].append({'date':d,'url':CONFIG['url']+href(issue_path(p)), 'path':issue_path(p), 'cutoff':p['research_cutoff'], 'source_sha256':hashlib.sha256(p['_path'].read_bytes()).hexdigest(), 'article_ids':[a['id'] for a in p['articles']], 'images':[a['image']['path'] for a in p['articles'] if a.get('image')]})
    hero = '<section class="hero"><div class="eyebrow">WEEKLY NEWS · KOREAN LEARNING ARCHIVE</div><h1>세상을 읽는 시간</h1><p class="lead">뉴스를 아는 데서, 세상을 이해하는 데로.<br>한 주의 중요한 변화를 배경과 질문으로 이어 읽습니다.</p><div class="meta">세계정세 · 한국사회 · 문화예술 · 과학기술 · 자연과학</div></section>'
    if posts:
        p=posts[0]
        latest=f'<section class="latest"><div class="eyebrow">최신 브리핑 · {p["publication_date"]}</div><h2><a href="{href(issue_path(p))}">{e(p["title"])}</a></h2><p class="meta">15개 기사로 읽는 다섯 분야 · 조사 기준 {e(p["research_cutoff_label"])} KST</p><a class="button" href="{href(issue_path(p))}">이번 회차 읽기 →</a></section>'
    else:
        latest='<p class="empty">첫 브리핑을 준비하고 있습니다.</p>'
    write_page('', '최신 브리핑', hero+latest+'<h2>최근 발행</h2>'+edition_list(posts[:8])+f'<p><a href="{href("archive/")}">연도·월별 전체 아카이브 →</a></p>')
    years=''.join(f'<a class="pill" href="{href("archive/"+y+"/")}">{y}년 · {len(by_year[y])}회</a>' for y in sorted(by_year, reverse=True))
    write_page('archive', '전체 아카이브', '<div class="eyebrow">ARCHIVE</div><h1>발행의 기록</h1><p class="lead">회차 발행일을 기준으로 연도와 월을 찾아보세요.<br>뉴스가 다루는 기간은 각 회차에 따로 표시합니다.</p><div class="archive-years">'+years+'</div>'+edition_list(posts))
    for year, group in by_year.items():
        months=''.join(f'<a class="pill" href="{href("archive/"+year+"/"+m[5:7]+"/")}">{int(m[5:7])}월 · {len(by_month[m])}회</a>' for m in sorted(by_month, reverse=True) if m.startswith(year))
        write_page(f'archive/{year}', year+'년 아카이브', f'<div class="breadcrumbs"><a href="{href("archive/")}">전체 아카이브</a></div><h1>{year}년</h1><div class="archive-years">{months}</div>'+edition_list(group))
    for month, group in by_month.items():
        write_page('archive/'+month.replace('-','/'), month+' 아카이브', f'<div class="breadcrumbs"><a href="{href("archive/")}">전체</a> / <a href="{href("archive/"+month[:4]+"/")}">{month[:4]}년</a></div><h1>{month[:4]}년 {int(month[5:7])}월</h1>'+edition_list(group))
    write_page('404', '페이지를 찾을 수 없습니다', f'<h1>페이지를 찾을 수 없습니다.</h1><p><a href="{href("archive/")}">전체 아카이브에서 회차 찾기</a></p>')
    shutil.copyfile(OUT/'404/index.html', OUT/'404.html')
    (OUT/'publication-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    public_paths=['', 'archive/']+[issue_path(p) for p in posts]+[f'archive/{y}/' for y in by_year]+[f'archive/{m.replace("-","/")}/' for m in by_month]
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+e(CONFIG['url']+href(p))+'</loc></url>' for p in public_paths)+'</urlset>', encoding='utf-8')
    (OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+CONFIG['url']+href('sitemap.xml')+'\n', encoding='utf-8')
    assert not any((OUT/x).exists() for x in ['.ops','docs','scripts','AGENTS.md','README.md','templates']), '운영 파일 배포 금지'
    from verify_local import verify
    verify(OUT, BASE)
    print(f'Built {len(posts)} issues / {len(posts)*15} articles; local links and public file allowlist verified.')

if __name__ == '__main__':
    build()
