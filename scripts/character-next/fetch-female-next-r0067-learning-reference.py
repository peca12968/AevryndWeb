"""Bounded publisher demo data download, reference only, no software install."""
from pathlib import Path
import urllib.request,json,time,hashlib,re
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0067-native-eve';D=R/'Reference/character/blender-bystedt-hair-cc-by-sa';D.mkdir(parents=True,exist_ok=True)
def main():
    tick=time.time();page='https://www.blender.org/download/demo-files/';headers={'User-Agent':'Mozilla/5.0','Cache-Control':'no-cache'}
    html=urllib.request.urlopen(urllib.request.Request(page,headers=headers),timeout=20).read().decode();needle='hair_nodes-female_hair_styles.blend';pos=html.index(needle);snippet=re.sub('<[^>]+>',' ',html[pos:pos+3000]);assert 'CC-BY-SA' in snippet and 'Daniel Bystedt' in snippet
    url='https://download.blender.org/demo/geometry-nodes/hair_nodes-female_hair_styles.blend';out=D/'hair_nodes-female_hair_styles.blend';expected=28612482
    if not out.exists():
        partial=out.with_suffix('.partial');total=0
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30) as response,partial.open('wb') as dst:
            assert response.status==200 and 'text/html' not in response.headers.get('Content-Type','')
            while block:=response.read(1024*1024):
                total+=len(block);assert total<=32*1024*1024 and time.time()-tick<60;dst.write(block)
        assert total==expected;partial.replace(out)
    assert out.stat().st_size==expected and hashlib.sha256(out.read_bytes()).hexdigest()=='1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48'
    row={'purpose':'Learning reference for next full-hair authoring basis, not an imported engine asset or a new r67 candidate.','publisherPage':page,'fileURL':url,'author':'Daniel Bystedt','listedLicense':'CC-BY-SA, version not established by the publisher card; verify embedded/source license before any derivative redistribution. Not CC0 or exclusive Aevrynd ownership.','file':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'softwareOrAddonInstalled':False,'embeddedCodeExecuted':False,'importedIntoEngineOrWorkingCharacter':False,'previousPageFileLinkReturnedHTML':True,'officialDownloadHostRangeProbeBytes':expected,'nextStep':'Open original demo read-only with auto-execution disabled, bound evaluated resources and inspect original complete hairstyle/guides/surface attachments and license. Learn generic authoring principles; do not automatically transplant/share-alike assets into own-engine formal assets.','seconds':time.time()-tick}
    text=json.dumps(row,ensure_ascii=False,indent=2)+'\n';(D/'PROVENANCE.json').write_text(text,encoding='utf8');(E/'next-learning-reference.json').write_text(text,encoding='utf8');print('R67_NEW_LEARNING_REFERENCE',out.stat().st_size,row['sha256'],time.time()-tick,flush=True)
if __name__=='__main__':main()
