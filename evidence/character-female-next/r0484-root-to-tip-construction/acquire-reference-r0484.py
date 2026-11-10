from pathlib import Path
from hashlib import file_digest,sha256
import subprocess
import json
import re
import os
ROOT=Path(__file__).resolve().parent
REPO=Path('F:/AevryndStorage/CharacterHistoryGit')
HEAD='1c5581f9616201ce5a2dfff58a4cf8b09988e5cd'
PREFIX='assets-source/aevrynd-character/female-next/r0126-evidence/'
NAMES=('AFN126_ORIGINAL_Hair_Hair_0-original-geometry.npz','original-artist-head-inspection.json',
       'reference-and-rights.json','source-acquisition-summary.json','prepare-aevrynd-r0126.py',
       'matched-original-artist-head-reference-oblique.png','matched-original-artist-head-reference-profile.png')
def sha(path):
    with path.open('rb') as f:return file_digest(f,'sha256').hexdigest()
folder=ROOT/'reference';folder.mkdir(exist_ok=False)
receipt={}
for name in NAMES:
    blob=subprocess.run(['git','show',HEAD+':'+PREFIX+name],cwd=REPO,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
    pointer=re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([a-f0-9]{64})\nsize ([0-9]+)\n',blob)
    dest=folder/name
    if pointer:
        env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='0'
        with dest.open('xb') as out,(ROOT/'reference-download.err').open('ab') as err:
            subprocess.run(['git','-c','lfs.storage='+(ROOT/'reference-lfs-cache').as_posix(),'-c','lfs.skipdownloaderrors=false',
                'lfs','smudge','--',PREFIX+name],input=blob,cwd=REPO,env=env,stdout=out,stderr=err,check=True)
        assert sha(dest)==pointer[1].decode() and dest.stat().st_size==int(pointer[2])
    else:dest.write_bytes(blob)
    receipt[name]=dict(path=str(dest),sha256=sha(dest),bytes=dest.stat().st_size,repositoryPath=PREFIX+name)
    print('R484_REFERENCE',name,dest.stat().st_size,flush=True)
(ROOT/'reference-acquisition.json').write_bytes(json.dumps(dict(commit=HEAD,files=receipt),indent=2).encode('utf8'))
