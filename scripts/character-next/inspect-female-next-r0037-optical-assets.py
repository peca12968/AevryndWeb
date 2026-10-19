"""Bounded explicit-CC0 eye-pigment reference index, no full pack download."""
import importlib.util,json,zipfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('f',Path(__file__).with_name('fetch-female-next-r0011-skin-assets.py'));f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0037-eye-margin'
def main():
    remote=f.RemoteZip(f.URL)
    with zipfile.ZipFile(remote) as z:rows=[{'name':i.filename,'bytes':i.file_size,'compressed':i.compress_size} for i in z.infolist() if (i.filename.startswith('eyes/') or i.filename.startswith('eyelashes/')) and not i.is_dir()]
    meta={'url':f.URL,'etag':remote.etag,'entries':rows,'transferredBytes':sum(r['bytes'] for r in remote.requests)};(E/'cc0-optical-index.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8');print(json.dumps(meta))
if __name__=='__main__':main()
