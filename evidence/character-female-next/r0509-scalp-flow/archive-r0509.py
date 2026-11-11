"""Stage and verify precisely the r0509 research archive."""
from pathlib import Path
from hashlib import file_digest, sha256
import json
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
REPO=Path('F:/AevryndStorage/CharacterHistoryGit')
SOURCE=Path('assets-source/aevrynd-character/female-next/r0509-source')
EVIDENCE=Path('evidence/character-female-next/r0509-scalp-flow')
PARENT='e01577dbe2edbf97cfbe91d6f2e32d4220e09b17'
BRANCH='character-history-v249'
REMOTE='https://github.com/peca12968/AevryndWeb.git'
ATTRIBUTES=(f'\n# r0509 scalp flow research\n'
            f'{SOURCE.as_posix()}/*.blend filter=lfs diff=lfs merge=lfs -text\n'
            f'{SOURCE.as_posix()}/*.npz filter=lfs diff=lfs merge=lfs -text\n'
            f'{EVIDENCE.as_posix()}/** -filter -diff -merge -text\n').encode()


def git(*args):
    return subprocess.run(['git',*args],cwd=REPO,check=True,stdout=subprocess.PIPE).stdout


def fingerprint(path):
    with path.open('rb') as stream:
        return dict(bytes=path.stat().st_size,sha256=file_digest(stream,'sha256').hexdigest())


def read(name):
    return json.loads((ROOT/name).read_bytes())


def copy_archive():
    assert git('rev-parse','HEAD').decode().strip()==PARENT
    assert git('branch','--show-current').decode().strip()==BRANCH
    assert git('remote','get-url','origin').decode().strip()==REMOTE
    assert not git('status','--porcelain=v1')
    assert not (REPO/SOURCE).exists() and not (REPO/EVIDENCE).exists()
    report=read('r0509-review.json')
    construction=read('construction-receipt.json')
    preview=read('preview-receipt.json')
    assert report['source']==construction['source']==preview['source']
    source=Path(report['source']['path'])
    bank=Path(construction['guideBank']['path'])
    assert fingerprint(source)=={k:report['source'][k] for k in ('sha256','bytes')}
    assert fingerprint(bank)['sha256']==construction['guideBank']['sha256']
    assert report['decision'] in ('RETAIN_R0509_A_LOCAL_RESEARCH','RETAIN_R0509_B_LOCAL_RESEARCH','REJECT_R0509_KEEP_R0507')
    names=[
        'work-card.txt','author-r0509.py','preview-r0509.py','contact-r0509.py','trace-contact-r0509.py',
        'run-r0509.ps1','measure-front-r0509.ps1','make-review-r0509.ps1','make-report-r0509.py','archive-r0509.py',
        'remote-range-readback-r0509.py','probe-lfs-range-r0509.py',
        'front-silhouette.json','construction-receipt.json','reopen-verification.json','preview-receipt.json',
        'r0509-review.json','visual-decision.json','r0509-frontal-comparison.png','r0509-body-comparison.png',
        'r0509-profile-comparison.png','skin-contact.json','failure-location.json','temple-turns.json','resources-r0509.json','render-cache-receipt.json',
    ]
    names.extend(Path(row['path']).name for row in preview['renders'].values())
    for stem in ('author','author-retry','preview','preview-resume','preview-tail',
                 'contact','contact-resume','contact-final','contact-tail'):
        if (ROOT/f'{stem}.log').is_file():
            names.extend((f'{stem}.log',f'{stem}.err'))
    assert len(names)==len(set(names))
    assert all((ROOT/name).is_file() for name in names)
    (REPO/SOURCE).mkdir(parents=True)
    (REPO/EVIDENCE).mkdir(parents=True)
    for path in (source,bank):
        shutil.copyfile(path,REPO/SOURCE/path.name)
    shutil.copytree(REPO/SOURCE.with_name('r0507-source')/'licenses',REPO/SOURCE/'licenses')
    readme=(ROOT/'README-r0509.md').read_text(encoding='utf-8').rstrip()+'\n'
    (REPO/SOURCE/'README.md').write_bytes(readme.encode())
    for name in names:
        shutil.copyfile(ROOT/name,REPO/EVIDENCE/name)
    manifest={}
    for root in (SOURCE,EVIDENCE):
        for path in sorted((REPO/root).rglob('*')):
            if path.is_file():
                manifest[path.relative_to(REPO).as_posix()]=fingerprint(path)
    data=json.dumps(manifest,indent=2).encode()
    (ROOT/'archive-package-manifest.json').write_bytes(data)
    (REPO/EVIDENCE/'archive-package-manifest.json').write_bytes(data)
    attributes=REPO/'.gitattributes'
    original=git('show','HEAD:.gitattributes')
    assert attributes.read_bytes()==original
    attributes.write_bytes(original+ATTRIBUTES)
    git('sparse-checkout','add',SOURCE.as_posix()+'/',EVIDENCE.as_posix()+'/')
    git('add','--','.gitattributes',SOURCE.as_posix(),EVIDENCE.as_posix())


def verify_archive():
    manifest_path=ROOT/'archive-package-manifest.json'
    manifest=json.loads(manifest_path.read_bytes())
    manifest[(EVIDENCE/manifest_path.name).as_posix()]=fingerprint(manifest_path)
    expected=set(manifest)|{'.gitattributes'}
    staged=set(git('diff','--cached','--name-only','-z').decode().strip('\0').split('\0'))
    assert staged==expected,(staged-expected,expected-staged)
    assert git('rev-parse','HEAD').decode().strip()==PARENT and not git('diff','--name-only')
    assert git('show',':.gitattributes')==git('show','HEAD:.gitattributes')+ATTRIBUTES
    git('diff','--cached','--check')
    assets=[]
    for name,entry in manifest.items():
        path=REPO/name
        assert fingerprint(path)==entry,name
        blob=git('show',':'+name)
        pointer=re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([a-f0-9]{64})\nsize ([0-9]+)\n',blob)
        if path.suffix in ('.blend','.npz'):
            assert pointer is not None,name
            oid,size=pointer[1].decode(),int(pointer[2])
            assert oid==entry['sha256'] and size==entry['bytes'],name
            cached=REPO/'.git/lfs/objects'/oid[:2]/oid[2:4]/oid
            assert fingerprint(cached)==entry,name
            assets.append(dict(path=name,oid=oid,bytes=size))
        else:
            assert len(blob)==entry['bytes'] and sha256(blob).hexdigest()==entry['sha256'],name
    assert len(assets)==2
    proof=dict(parent=PARENT,branch=BRANCH,exactStagedScopeVerified=True,
        files=len(staged),lfsFiles=assets,lfsBytes=sum(x['bytes'] for x in assets))
    (ROOT/'archive-staging-verification.json').write_bytes(json.dumps(proof,indent=2).encode())
    print(json.dumps(proof,indent=2),flush=True)


if __name__=='__main__':
    if sys.argv[1:]!=['--verify-only']:
        copy_archive()
    verify_archive()

