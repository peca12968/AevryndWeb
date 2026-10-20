"""Fetch pinned CC0 character data only; no addon or embedded code execution."""
from pathlib import Path
import urllib.request,hashlib,json,time
R=Path(r'D:\Download\Aevrynd');D=R/'Reference/character/charmorph-vitruvian-cc0/r0069-rig-data';E=R/'Evidence/character-female-next/r0069-complete-controls';REV='c252d1fc7f00ba59d87b66b3d32fa3471fc6ee44'
def main():
    tick=time.time();D.mkdir(parents=True,exist_ok=True);E.mkdir(parents=True,exist_ok=True);rows=[]
    for name in ('rigs.blend','weights/mixamo.npz','joints/Mixamo.npz'):
        p=D/name;p.parent.mkdir(parents=True,exist_ok=True);url='https://raw.githubusercontent.com/Upliner/CharMorph-Vitruvian/'+REV+'/'+name
        if not p.exists():
            with urllib.request.urlopen(url,timeout=25) as f:data=f.read(32*1024*1024+1)
            assert len(data)<=32*1024*1024
            if data.startswith(b'version https://git-lfs.github.com/spec/'):
                url='https://media.githubusercontent.com/media/Upliner/CharMorph-Vitruvian/'+REV+'/'+name
                with urllib.request.urlopen(url,timeout=25) as f:data=f.read(32*1024*1024+1)
                assert len(data)<=32*1024*1024
            assert data.startswith(b'BLENDER') if name.endswith('.blend') else data.startswith(b'PK');p.write_bytes(data)
        rows.append({'file':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pinnedURL':url})
    out={'source':'https://github.com/Upliner/CharMorph-Vitruvian','commit':REV,'declaredLicense':'CC0 in existing pinned config.yaml','authors':'Sean Buckley, Olaf Delgado-Friedrichs; original full credits in parent config.yaml','configSha256':hashlib.sha256((D.parent/'config.yaml').read_bytes()).hexdigest(),'scope':'Only regular bone, source-indexed weight and joint data. Mixamo is a source skeleton label, no Adobe/Mixamo service, code or animation used.','files':rows,'addonInstalled':False,'sourceCodeExecuted':False,'seconds':time.time()-tick}
    text=json.dumps(out,ensure_ascii=False,indent=2)+'\n';(D/'PROVENANCE.json').write_text(text,encoding='utf8');(E/'rig-data-provenance.json').write_text(text,encoding='utf8');print('R69_FETCH_DATA',[(x['file'],x['bytes']) for x in rows],time.time()-tick)
if __name__=='__main__':main()
