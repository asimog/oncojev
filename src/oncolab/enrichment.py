"""Targeted public package/repository enrichment; no installation or ingestion."""
import hashlib
import json
import re
from html.parser import HTMLParser
from urllib.parse import urljoin

from src.oncolab.discovery import ExternalCapabilityCandidate, ExternalLookup
from src.provenance import content_hash


class PackagePage(HTMLParser):
    """Extract package table facts and source/doc links from one official page."""
    def __init__(self):
        super().__init__()
        self.text=[];self.links=[];self.cells=[];self._cell=None;self.description=None
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='meta' and attrs.get('name')=='description':self.description=attrs.get('content')
        if tag=='a' and attrs.get('href'):self.links.append(attrs['href'])
        if tag=='td':self._cell=[]
    def handle_data(self,data):
        if self._cell is not None:self._cell.append(data)
        self.text.append(data)
    def handle_endtag(self,tag):
        if tag=='td' and self._cell is not None:
            self.cells.append(' '.join(''.join(self._cell).split()));self._cell=None


async def describe_package(client,source,identity):
    responses=[]
    async def get(url,params=None):
        response=await client._get(url,params or {})
        responses.append(response)
        if sum(len(r.content) for r in responses)>client.max_bytes:raise ValueError('enrichment aggregate byte ceiling exceeded')
        return response
    if source=='github':
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',identity):raise ValueError('declare owner/repository')
        base='https://api.github.com/repos/'+identity
        repo=(await get(base)).json()
        if repo.get('private') is not False or str(repo.get('full_name','')).casefold()!=identity.casefold():
            raise ValueError('public repository identity required')
        commit=(await get(base+'/commits/'+repo['default_branch'])).json()
        sha=commit.get('sha')
        if not re.fullmatch(r'[0-9a-f]{40}',sha or ''):raise ValueError('unresolved immutable GitHub commit')
        tree=(await get(base+'/git/trees/'+sha)).json()
        entries=tree.get('tree') or []
        paths=[item['path'] for item in entries if item.get('type') in {'blob','tree'}]
        relevant=[path for path in paths if path.lower().startswith(('readme','license','requirements','pyproject','setup','environment','dockerfile','description','namespace','tests','vignettes'))]
        card=ExternalCapabilityCandidate(source=source,external_id=identity,name=repo.get('name',identity),
            description=repo.get('description') or '',homepage=repo.get('html_url'),
            licence=(repo.get('license') or {}).get('spdx_id'),versions=(sha,),
            links=tuple({'url':repo['html_url']+('/tree/' if any(e.get('path')==path and e.get('type')=='tree' for e in entries) else '/blob/')+sha+'/'+path,'type':'source_reference'} for path in relevant[:20]),
            metadata={'commit_sha':sha,'default_branch':repo['default_branch'],'language':repo.get('language'),
                      'root_paths':paths[:40],'tree_truncated':bool(tree.get('truncated'))},
            omissions=('root references truncated',) if len(paths)>40 or len(relevant)>20 else (),
            limitations=('Public access is not a licence grant. References require canonical-operation inspection before qualification.',))
    elif source=='bioconda':
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,150}',identity):raise ValueError('invalid Bioconda package')
        body=(await get('https://api.anaconda.org/package/bioconda/'+identity)).json()
        if body.get('name')!=identity:raise ValueError('Bioconda package identity mismatch')
        version=body.get('latest_version')
        files=[f for f in body.get('files',[]) if f.get('version')==version]
        # Each build retains dependencies/checksum/platform; no arbitrary Conda install.
        builds=[{'basename':f.get('basename'),'version':f.get('version'),'md5':f.get('md5'),
            'sha256':f.get('sha256'),'platform':f.get('attrs',{}).get('subdir'),
            'dependencies':f.get('attrs',{}).get('depends',[])[:40], 'build':f.get('attrs',{}).get('build')}
            for f in files[:10]]
        card=ExternalCapabilityCandidate(source=source,external_id=identity,name=body['name'],
            description=body.get('summary') or '',homepage=body.get('home'),licence=body.get('license'),
            versions=(version,) if version else (),metadata={'builds':builds,'runtime':'Conda backend unsupported'},
            links=({'url':'https://github.com/bioconda/bioconda-recipes/tree/master/recipes/'+identity,'type':'uninspected_recipe_reference'},),
            omissions=('additional builds omitted',) if len(files)>10 else (),
            limitations=('Metadata only; no Conda installation or verified execution environment.',))
    elif source=='bioconductor':
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9.]{0,149}',identity):raise ValueError('invalid Bioconductor package')
        url='https://bioconductor.org/packages/release/bioc/html/'+identity+'.html'
        response=await get(url)
        page=PackagePage();page.feed(response.text)
        text=' '.join(page.text)
        if not re.search(r'<h1[^>]*>\s*'+re.escape(identity)+r'\s*</h1>',response.text):
            raise ValueError('Bioconductor package identity mismatch')
        details=dict(zip(page.cells[::2],page.cells[1::2]))
        version=re.search(r'Package version:\s*([0-9.]+)',text)
        release=re.search(r'Bioconductor version:\s*([0-9.]+)',text)
        references=[urljoin(url,link) for link in page.links if any(part in link for part in ('vignettes/','manuals/','src/contrib/','github.com/','checkResults/'))]
        card=ExternalCapabilityCandidate(source=source,external_id=identity,name=identity,
            description=page.description or '',homepage=url,licence=details.get('License'),
            versions=(version.group(1),) if version else (),links=tuple({'url':link,'type':'documentation_or_source'} for link in references[:20]),
            metadata={'release':release.group(1) if release else None,'biocViews':details.get('biocViews'),
                      'dependencies':text[text.find('Dependencies'):text.find('Reverse dependencies')][:4000],
                      'source_branch':details.get('Source branch'),'runtime':'R backend unsupported'},
            omissions=('additional references omitted',) if len(references)>20 else (),
            limitations=('Metadata only; no supported verified R execution environment. Build status unmeasured unless an exact report is inspected.',))
    else:raise ValueError('unsupported enrichment source')
    raw=[{'url':str(r.url),'sha256':hashlib.sha256(r.content).hexdigest(),'body':r.text} for r in responses]
    return ExternalLookup(source=source,operation='describe',request={'external_id':identity},
        response_sha256=content_hash([r['sha256'] for r in raw]),response_bytes=sum(len(r.content) for r in responses),
        raw_json=json.dumps(raw),cards=(card,),limitations=('Retained response bundle hashes exact bodies; package metadata is mutable and not execution authority.',))
