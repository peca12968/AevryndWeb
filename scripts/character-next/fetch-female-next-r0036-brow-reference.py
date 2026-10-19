"""Fetch three small artist-authored CC0 brow textures for bounded comparison."""
import importlib.util, zipfile, json, hashlib
from pathlib import Path
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0036-data-informed-brows';D=R/'engine/assets/characters/female-next/source/brows/makehuman-system-cc0'
spec=importlib.util.spec_from_file_location('f',Path(__file__).with_name('fetch-female-next-r0011-skin-assets.py'));f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
def main():
    D.mkdir(parents=True,exist_ok=True);remote=f.RemoteZip(f.URL);rows=[]
    with zipfile.ZipFile(remote) as z:
        for name in ('eyebrow001','eyebrow009','eyebrow010'):
            for ext in ('.png','.obj','.mhmat'):
                key=f'eyebrows/{name}/{name}{ext}';p=D/(name+ext)
                if p.exists():raise RuntimeError('Do not overwrite prior donor: '+str(p))
                data=z.read(key);p.write_bytes(data);rows.append({'archiveEntry':key,'localPath':str(p),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'crc32':f'{z.getinfo(key).CRC:08x}'})
    meta={'sourceURL':f.URL,'etag':remote.etag,'archiveBytes':remote.size,'license':'CC0-1.0','licenseEvidence':['https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html','https://static.makehumancommunity.org/about/license.html'],'origin':'MakeHuman Community system graphical assets; artist-authored donors, not Aevrynd originals','codeImported':False,'files':rows,'requests':remote.requests,'totalTransferredBytes':sum(x['bytes'] for x in remote.requests),'scope':'Reference donors only until actual mapping and 3D morphology validated; no automatic formal-asset promotion.'}
    (D/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8');(E/'brow-download-provenance.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8');print(json.dumps({'files':len(rows),'transferred':meta['totalTransferredBytes']}))
if __name__=='__main__':main()
