from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.ids=set()
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs: self.ids.add(attrs['id'])
        for key in ['href','src']:
            if key in attrs: self.links.append(attrs[key])

def verify(root:Path,base:str):
    cache={}
    for file in root.rglob('*.html'):
        p=Links();p.feed(file.read_text(encoding='utf-8'));cache[file.resolve()]=p
    for file,p in cache.items():
        for link in p.links:
            u=urlsplit(link)
            if u.scheme or u.netloc:continue
            if not u.path:target=file
            elif u.path.startswith(base+'/'):
                target=root/unquote(u.path[len(base)+1:])
            elif u.path.startswith('/'):
                raise ValueError(f'프로젝트 경로 누락: {file}: {link}')
            else:target=file.parent/unquote(u.path)
            if target.is_dir():target=target/'index.html'
            assert target.is_file(),f'깨진 내부 링크: {file}: {link}'
            if u.fragment and target.suffix=='.html':
                assert unquote(u.fragment) in cache[target.resolve()].ids,f'깨진 기사 앵커: {link}'
