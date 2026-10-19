"""Fetch only pinned character data, not software or executable tool code."""
from pathlib import Path
import urllib.request,json,hashlib,time
R=Path(r'D:\Download\Aevrynd');D=R/'Reference/character/charmorph-vitruvian-cc0';T=D/'textures-4k';T.mkdir(parents=True,exist_ok=True)
REV='c252d1fc7f00ba59d87b66b3d32fa3471fc6ee44';BASE=f'https://raw.githubusercontent.com/Upliner/CharMorph-Vitruvian/{REV}/'
names=[f'{kind}.{tile}.exr' for kind in ('Light_Skin_Color','Skin_Roughness','Skin_Height') for tile in range(1001,1005)]+['Sclera_Color.1005.exr','Iris_Color.1007.exr','Mouth_Color.1008.exr']
rows=[];tick=time.time()
for name in names:
    p=T/name;url=BASE+'textures/4K/'+name
    if not p.exists():
        with urllib.request.urlopen(url,timeout=45) as src,p.open('wb') as dst:
            while chunk:=src.read(1024*1024):dst.write(chunk)
    assert p.read_bytes()[:4]==b'v/1\x01',('Expected OpenEXR',name)
    rows.append({'file':name,'url':url,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    print('R57_PINNED_TEXTURE',name,p.stat().st_size,flush=True)
(D/'r0057-texture-provenance.json').write_text(json.dumps({'repository':'https://github.com/Upliner/CharMorph-Vitruvian','commit':REV,
    'license':'CC0 declared by source config.yaml; author and contributor credits retained there. Source data only, not addon code.',
    'authors':'Sean Buckley, Olaf Delgado-Friedrichs, additional contributors in config.yaml','files':rows,'seconds':time.time()-tick},indent=2)+'\n',encoding='utf8')
print('R57_TEXTURES_READY',sum(x['bytes'] for x in rows),time.time()-tick,flush=True)
