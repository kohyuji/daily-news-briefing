"""Integration checks for rollover, in-place reruns, source fidelity and hidden ops."""
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.vendor'))
from build import read_post
qa_root=ROOT/'.qa'
assert qa_root.resolve().parent==ROOT.resolve()
qa_root.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='briefing-build-',dir=qa_root) as temp:
    target=Path(temp)
    assert target.resolve().parent==qa_root.resolve()
    for name in ['scripts','templates','assets']:
        shutil.copytree(ROOT/name,target/name,ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copyfile(ROOT/'site.json',target/'site.json')
    (target/'_posts').mkdir()
    post=read_post(ROOT/'_posts'/'2026-11-12-briefing.md')
    for key in ['_body','_path']:post.pop(key)
    body=read_post(ROOT/'_posts'/'2026-11-12-briefing.md')['_body']
    # Exercise adjacent publication months and a year boundary without publishing fixtures.
    for date in ['2026-12-31','2027-01-01']:
        meta=dict(post)
        meta['publication_date']=date
        meta['published_at']=date+'T11:00:00+09:00'
        meta['articles']=[dict(a,image=None) for a in post['articles']]
        import re
        fixture=re.sub(r'!\[[^\]]*\]\([^\n]+\)','관련 이미지 미확보',body)
        (target/'_posts'/f'{date}-briefing.md').write_text('---\n'+json.dumps(meta,ensure_ascii=False)+'\n---\n'+fixture,encoding='utf-8')
    environment=__import__('os').environ.copy()
    environment['PYTHONPATH']=str(ROOT/'.vendor')
    command=[sys.executable,str(target/'scripts/build.py')]
    subprocess.run(command,env=environment,check=True,capture_output=True)
    generated=target/'_site'
    for path in ['archive/2026/12/index.html','archive/2027/01/index.html','archive/2026/index.html','archive/2027/index.html']:
        assert (generated/path).is_file(),path
    assert '2027-01-01' in (generated/'index.html').read_text(encoding='utf-8')
    before={str(p.relative_to(generated)):p.read_bytes() for p in generated.rglob('*') if p.is_file()}
    subprocess.run(command,env=environment,check=True,capture_output=True)
    after={str(p.relative_to(generated)):p.read_bytes() for p in generated.rglob('*') if p.is_file()}
    assert before==after,'Repeated build changed output or duplicated an issue'
    assert not any((generated/x).exists() for x in ['.ops','docs','templates','scripts','AGENTS.md'])
    assert len(json.loads((generated/'publication-manifest.json').read_text(encoding='utf-8'))['issues'])==2
print('PASS: year/month rollover, newest-first home, deterministic rerun, two unique editions, hidden operations.')
