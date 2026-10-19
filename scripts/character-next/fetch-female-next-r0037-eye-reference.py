"""Selected explicitly CC0 graphical reference data, never program import."""
import importlib.util,zipfile,json,hashlib
from pathlib import Path
spec=importlib.util.spec_from_file_location('f',Path(__file__).with_name('fetch-female-next-r0011-skin-assets.py'));f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0037-eye-margin';D=S/'eyes/makehuman-system-cc0'
def main():
    D.mkdir(parents=True,exist_ok=True);remote=f.RemoteZip(f.URL);rows=[]
    with zipfile.ZipFile(remote) as z:
        for key in ('eyes/materials/brown_eye.png','eyes/materials/brown.mhmat','eyes/high-poly/high-poly.obj','eyelashes/eyelashes01/eyelashes01.png','eyelashes/eyelashes01/eyelashes01.mhmat'):
            path=D/Path(key).name
            if path.exists():raise RuntimeError('Do not overwrite donor '+str(path))
            data=z.read(key);path.write_bytes(data);rows.append({'archiveEntry':key,'localPath':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'crc32':f'{z.getinfo(key).CRC:08x}'})
    metadata={'sourceURL':f.URL,'etag':remote.etag,'archiveBytes':remote.size,'license':'CC0-1.0','explicitLicenseEvidence':'Downloaded .mhmat and .obj headers explicitly release these graphical assets as CC0 in September2020.','copyrightAtRelease':['Data Collection AB','Joel Palmius','Jonas Hauquier'],'codeImported':False,'files':rows,'transferredBytes':sum(r['bytes'] for r in remote.requests),'scope':'Data references until validated; donor eyeball geometry and shader program will not be imported.'};(D/'provenance.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf8');(E/'cc0-eye-download-provenance.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf8');print(json.dumps({'files':len(rows),'transferredBytes':metadata['transferredBytes']}))
if __name__=='__main__':main()
