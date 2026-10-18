"""Selective official core asset download, verified ranges and ZIP CRCs."""
import json,zipfile,hashlib,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('fetch',Path(__file__).with_name('fetch-female-next-r0011-skin-assets.py'));fetch=importlib.util.module_from_spec(spec);spec.loader.exec_module(fetch)
R=fetch.R;E=R/'Evidence/character-female-next/r0024-oral-layers';D=R/'engine/assets/characters/female-next/source/oral/makehuman-system-cc0';E.mkdir(exist_ok=True);D.mkdir(parents=True,exist_ok=True)
def main():
    remote=fetch.RemoteZip(fetch.URL);results=[]
    with zipfile.ZipFile(remote) as archive:
        entries=[i for i in archive.infolist() if i.filename.startswith(('teeth/teeth_base/','tongue/tongue01/')) and not i.is_dir()]
        for entry in entries:
            relative=Path(entry.filename);assert not relative.is_absolute() and '..' not in relative.parts;assert entry.file_size<16*1024*1024;content=archive.read(entry);dest=D/relative;dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():assert dest.read_bytes()==content
            else:dest.write_bytes(content)
            results.append({'archivePath':entry.filename,'path':str(dest),'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),'zipCRC32':f'{entry.CRC:08x}'})
    proof={'url':fetch.URL,'etag':remote.etag,'archiveBytes':remote.size,'files':results,'rangeRequests':remote.requests,'totalTransferredBytes':sum(x['bytes'] for x in remote.requests),'officialLicenseReference':'https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html','programImported':False,'licensePolicy':'Read per-file metadata before integration; reuse graphical assets only, with original credit, not MPFB program code.'};(E/'download-provenance.json').write_text(json.dumps(proof,indent=2)+'\n');(D/'r0024-download-provenance.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'files':[(r['archivePath'],r['bytes']) for r in results],'transferredBytes':proof['totalTransferredBytes']},indent=2))
if __name__=='__main__':main()
