"""Fetch one licensed public Objaverse model with exact original attribution.
Sketchfab official anonymous download requires authentication; do not bypass it.
Use the independent public Ai2 dataset release and verify its per-object metadata.
"""
from pathlib import Path
import urllib.request,json,gzip,hashlib,time,datetime
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0126-individual-head-foundation';D=R/'engine/assets/characters/female-next/source/r0126-source/individual-head-input';UID='27f75fa94c384000bb6a79a3000f8e80'
def request(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'AevryndCharacterResearch/1.0'}),timeout=30)
def save(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 tick=time.time();D.mkdir(exist_ok=True);api='https://api.sketchfab.com/v3/models/'+UID
 with request(api) as response:current=json.load(response)
 assert current['license']['url'].rstrip('/')=='http://creativecommons.org/licenses/by/4.0' and current['isDownloadable']
 save(D/('sketchfab-'+UID+'-current-metadata.json'),current)
 repo={'sha':json.loads((D/'dataset-revision.json').read_text('utf-8'))['commit']}
 commit=repo['sha'];base='https://huggingface.co/datasets/allenai/objaverse/resolve/'+commit+'/'
 compressed=(D/'object-paths-original.json.gz').read_bytes()
 paths=json.loads(gzip.decompress(compressed));path=paths[UID];assert path.endswith(UID+'.glb');indexPath=D/'object-paths-original.json.gz';indexPath.write_bytes(compressed)
 metadataPath='metadata/'+path.split('/')[1]+'.json.gz'
 with request(base+metadataPath) as response:metaRaw=response.read()
 (D/'original-metadata-shard.json.gz').write_bytes(metaRaw);allmeta=json.loads(gzip.decompress(metaRaw));original=allmeta[UID];save(D/'selected-original-metadata.json',original)
 assert original['license']=='by' or (isinstance(original['license'],dict) and original['license'].get('slug')=='by'),original['license']
 target=D/('artist-head-'+UID+'.glb');url=base+path;sourceURL=url
 with request(url) as response:
  length=int(response.headers.get('Content-Length','0'));assert length<400000000
  with target.open('xb') as out:
   while data:=response.read(1048576):out.write(data)
  assert not length or target.stat().st_size==length
 assert target.read_bytes()[:4]==b'glTF'
 for name,url in [('CC-BY-4.0-legalcode.html','https://creativecommons.org/licenses/by/4.0/legalcode.en'),('objaverse-dataset-card.md','https://huggingface.co/datasets/allenai/objaverse/raw/'+commit+'/README.md')]:
  with request(url) as response:(D/name).write_bytes(response.read())
 save(D/'PROVENANCE.json',{'retrievedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalTitle':current['name'],'author':current['user']['displayName'],'authorProfile':current['user']['profileUrl'],'originalURL':current['viewerUrl'],'originalUID':UID,'assetLicense':current['license'],'dataset':'Ai2/Allen Institute for AI Objaverse1.0','datasetURL':'https://huggingface.co/datasets/allenai/objaverse','datasetCommit':commit,'datasetFilePath':path,'downloadURL':sourceURL,'metadataShardPath':metadataPath,'fullPublicGLBBytes':target.stat().st_size,'fullPublicGLBSha256':sha(target),'originalMetadataLicenseVerified':True,'currentOriginalMetadataLicenseVerified':True,'fullIndexAndMetadataShardPreserved':True,'databaseODCByNoticeSeparateFromIndividualCCBY4':True,'rights':'Credit the original named artist identified above, link original source and CC-BY4.0, mark modifications. Original source scan not exclusively owned. No asset-related royalties or engine runtime service, no program imported. Author license is not a measured anatomy/animation/full rights/likeness release qualification.','files':[{'file':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(D.iterdir()) if p.is_file()]})
 save(E/'source-acquisition-summary.json',{'source':str(target),'sha256':sha(target),'bytes':target.stat().st_size,'inputDirectory':str(D),'provenance':str(D/'PROVENANCE.json'),'seconds':time.time()-tick,'notAnAdoptionOrAppearanceGain':True});print('R126_FULL_LICENSED_INDIVIDUAL_SOURCE_READY',target.stat().st_size,path,time.time()-tick,flush=True)
if __name__=='__main__':main()
