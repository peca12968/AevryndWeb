"""Stage and verify precisely the r0506 research archive."""
from pathlib import Path
from hashlib import file_digest, sha256
import json
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
REPO=Path('F:/AevryndStorage/CharacterHistoryGit')
SOURCE=Path('assets-source/aevrynd-character/female-next/r0506-source')
EVIDENCE=Path('evidence/character-female-next/r0506-guide-inertia')
PARENT='bebedacc1a5759c85dd3d8911f8a9eb6a34edd40'
BRANCH='character-history-v249'
REMOTE='https://github.com/peca12968/AevryndWeb.git'
ATTRIBUTES=(f'\n# r0506 guide inertia research\n'
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
    report=read('r0506-review.json')
    construction=read('construction-receipt.json')
    preview=read('preview-receipt.json')
    assert report['source']==construction['source']==preview['source']
    source=Path(report['source']['path'])
    bank=Path(construction['bank']['path'])
    assert fingerprint(source)=={k:report['source'][k] for k in ('sha256','bytes')}
    assert fingerprint(bank)['sha256']==construction['bank']['sha256']
    assert report['decision']=='REJECT_R0506_MOTION_KEEP_R0505_HAIRSTYLE'
    names=[
        'work-card.txt','author-r0506.py','preview-r0506.py','contact-r0506.py',
        'run-r0506.ps1','make-review-r0506.ps1','make-gif-r0506.py','make-report-r0506.py','archive-r0506.py',
        'remote-range-readback-r0506.py','probe-lfs-range-r0506.py',
        'construction-receipt.json','reopen-verification.json','preview-receipt.json',
        'r0506-review.json','r0506-head-comparison.png','r0506-body-comparison.png',
        'r0506-motion-comparison.png','r0506-hair-motion.gif',
        'skin-contact.json','projection-diagnostic.json','resources-r0506.json',
    ]
    names.extend(Path(row['path']).name for row in preview['renders'].values())
    for stem in ('author','author-retry','author-rna','preview','preview-resume','preview-final',
                 'contact','contact-resume'):
        if (ROOT/f'{stem}.log').is_file():
            names.extend((f'{stem}.log',f'{stem}.err'))
    assert len(names)==len(set(names))
    assert all((ROOT/name).is_file() for name in names)
    (REPO/SOURCE).mkdir(parents=True)
    (REPO/EVIDENCE).mkdir(parents=True)
    for path in (source,bank):
        shutil.copyfile(path,REPO/SOURCE/path.name)
    shutil.copytree(REPO/SOURCE.with_name('r0505-source')/'licenses',REPO/SOURCE/'licenses')
    shutil.copyfile(ROOT/'README-r0506.md',REPO/SOURCE/'README.md')
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

