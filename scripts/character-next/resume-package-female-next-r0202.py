"""One failed r202 source/current construction; preserve actual F storage and original clocks."""
from pathlib import Path
import json,hashlib,datetime,os,subprocess
access=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));R=Path(access['directProjectAccess']);C=Path(access['directCharacterArchiveAccess']);G=R/'sites-engine-journey';M=C/'assets-source/aevrynd-character/female-next';S=R/'engine/assets/characters/female-next/source';E=C/'evidence/character-female-next/r0202-independent-complete-groom'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,v):Path(p).write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def sha(p):return hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
def git(*args):
 env=os.environ.copy()
 for k in ['GIT_INDEX_FILE','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES']:env.pop(k,None)
 env.update(GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never',GOMAXPROCS='4');p=subprocess.run(['git','-c','core.autocrlf=false',*args],cwd=str(C),capture_output=True,env=env)
 if p.returncode:raise RuntimeError(p.stderr.decode('utf-8','replace'))
 return p.stdout

def sha(p):
 p=Path(p);p=p if p.is_absolute() else R/p;return hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
t=read(E/'before.json');b=read(E/'diagnostic-build-summary.json');audit=read(E/'continuation.json');working=audit['workingCompleteWomanReference'];assert not git('diff','--cached','--name-only')
shared=C/'scripts/character-next/finalize-package-female-next-r0191.py';assert sha(shared)=='d78ca974e1fbea7d5c6caeeb1b05ad26099816ca1a1e5f22fae05a5d608214dc';sharedText=shared.read_text('utf-8');tail="old=read(R/'Evidence"+sharedText.split("old=read(R/'Evidence",1)[1]
tail=tail.replace('range(152,192)','range(152,203)').replace('r0191-native-growth-volume','r0202-independent-complete-groom').replace('r0191','r0202')
start=tail.index("'reused190RootConstruction':");end=tail.index("'old331Nine",start);tail=tail[:start]+"'preservedOriginalFailedConstruction':{'source':str(E/'first-authoring.failed.py.txt'),'sha256':sha(E/'first-authoring.failed.py.txt'),'newGroomNotEmitted':True},"+tail[end:]
tail=tail.replace('r0184-native-follicle-deformation/history-copy-integrity.json','r0201-full-rest-native-volume/history-copy-integrity.json').replace('old331NineUnrelatedWorking139Input184External117AndDependenciesVerified','old331NineUnrelatedWorking139Input201External117AndDependenciesVerified')
tail=tail.replace("assert not link.exists();subprocess.check_call","assert not link.exists() or os.path.samefile(link,target);\n if not link.exists():subprocess.check_call")
tail=tail.replace("'noAdopt':65,'cadence':0,'nextWholeAfter':3","'noAdopt':76,'cadence':2,'nextWholeAfter':1").replace("'revision':'r191'","'revision':'r202'")
exec(tail)