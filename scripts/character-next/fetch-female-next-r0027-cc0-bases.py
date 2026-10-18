"""Fetch the observed official CC0 human-base bundle for the next foundation check.

Reference data only; do not install addons or change a character source here.
"""
import urllib.request,re,json,hashlib,zipfile
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0027-hair-redesign';F=R/'Reference/character/blender-human-base-meshes-v1.4.1';F.mkdir(parents=True,exist_ok=True)
PAGE='https://www.blender.org/download/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    req=urllib.request.Request(PAGE,headers={'User-Agent':'Aevrynd-character-authoring/1.0'})
    with urllib.request.urlopen(req,timeout=25) as response:html=response.read(512*1024).decode('utf8')
    links=re.findall(r'https://(?:mirror|download)\.blender\.org/[^\s"<>]+?\.zip',html);assert links,'No observed official direct link';url=links[0];dest=F/'human-base-meshes-bundle-v1.4.1.zip';total=0
    if not dest.exists():
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Aevrynd-character-authoring/1.0'}),timeout=30) as response, dest.open('wb') as output:
            while True:
                chunk=response.read(1024*1024)
                if not chunk:break
                total+=len(chunk);assert total<=60*1024*1024;output.write(chunk)
    with zipfile.ZipFile(dest) as archive:
        assert archive.testzip() is None;members=[{'name':m.filename,'bytes':m.file_size,'crc32':hex(m.CRC)} for m in archive.infolist()];notes=[]
        for m in archive.infolist():
            if m.filename.lower().endswith(('.txt','.md','.blend','.cats.txt')):
                target=(F/m.filename).resolve();assert target.is_relative_to(F.resolve())
                if m.is_dir():continue
                target.parent.mkdir(parents=True,exist_ok=True)
                with archive.open(m) as source,target.open('wb') as out:
                    while True:
                        chunk=source.read(1024*1024)
                        if not chunk:break
                        out.write(chunk)
                if target.suffix.lower() in ('.txt','.md'):notes.append({'name':m.filename,'text':target.read_text(encoding='utf8',errors='replace')[:12000]})
    result={'officialListing':'https://www.blender.org/download/demo-files/','listingDeclaration':'Human Base Meshes v1.4.1, Blender Studio and community contributions, 49 MB, CC0, updated Jan 20 2025.','downloadPage':PAGE,'observedDirectURL':url,'archive':str(dest),'sha256':sha(dest),'archiveBytes':dest.stat().st_size,'CRCVerified':True,'members':members,'embeddedNotes':notes,'use':'Reference-only foundation assessment; no source/model/runtime promotion.'};(E/'cc0-human-base-download.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps({'sha256':result['sha256'],'bytes':result['archiveBytes'],'members':members,'notes':notes},indent=2))
if __name__=='__main__':main()
