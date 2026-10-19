"""Fetch ONE verified core CC0 hairstyle from official pack using byte ranges.
Data only; does not install MakeHuman or another tool. Whole archive is never
downloaded when the mirror supports ranged reads. Exact selected bytes hashed.
"""
from pathlib import Path
import urllib.request,io,zipfile,json,hashlib,time
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0047-anatomical-hair';E.mkdir(exist_ok=True);OUT=R/'Reference/character/makehuman-core-bob02-cc0';OUT.mkdir(exist_ok=True)
URL='https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip'
class RemoteZip(io.RawIOBase):
    def __init__(self,url):
        self.url=url;self.pos=0;self.cache={};self.block=262144;self.downloaded=0;self.requests=0
        with urllib.request.urlopen(urllib.request.Request(url,headers={'Range':'bytes=0-0','User-Agent':'Aevrynd-asset-source/1.0'}),timeout=20) as r:
            assert r.status==206,('Mirror does not support exact ranges',r.status);self.size=int(r.headers['Content-Range'].split('/')[-1]);r.read()
    def seekable(self):return True
    def readable(self):return True
    def tell(self):return self.pos
    def seek(self,p,whence=0):self.pos=p if whence==0 else self.pos+p if whence==1 else self.size+p;return self.pos
    def read(self,n=-1):
        if n<0:n=self.size-self.pos
        end=min(self.size,self.pos+n);out=[]
        while self.pos<end:
            k=self.pos//self.block
            if k not in self.cache:
                lo=k*self.block;hi=min(self.size,lo+self.block)-1;assert self.requests<100 and self.downloaded<24*1024*1024,'Bounded selected-asset transfer limit'
                with urllib.request.urlopen(urllib.request.Request(self.url,headers={'Range':f'bytes={lo}-{hi}','User-Agent':'Aevrynd-asset-source/1.0'}),timeout=20) as r:
                    assert r.status==206;data=r.read();assert len(data)==hi-lo+1;self.cache[k]=data;self.requests+=1;self.downloaded+=len(data)
            data=self.cache[k];offset=self.pos%self.block;take=min(end-self.pos,len(data)-offset);out.append(data[offset:offset+take]);self.pos+=take
        return b''.join(out)
def main():
    t=time.time();remote=RemoteZip(URL)
    with zipfile.ZipFile(remote) as z:
        names=[n for n in z.namelist() if '/bob02/' in '/'+n.lower() and not n.endswith('/')];assert names,'bob02 missing from official pack';assert sum(z.getinfo(n).file_size for n in names)<24*1024*1024
        files=[]
        for name in names:
            info=z.getinfo(name);p=OUT/Path(name).name;data=z.read(info);p.write_bytes(data);files.append({'archivePath':name,'file':p.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()});print('R47_ASSET',p.name,len(data),flush=True)
    record={'sourceURL':URL,'officialManifestURL':'https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html','asset':'bob02','author':'makehuman_system (per official manifest; inspect file headers for original author)','license':'CC0 per explicit bob02 official table row, subject to exact file-header consistency check','packBytes':remote.size,'downloadedRangeBytes':remote.downloaded,'rangeRequests':remote.requests,'files':files,'purpose':'Single authored hairstyle geometry/texture/fitting-data for integration on same owned character, not another app installation','seconds':time.time()-t};(OUT/'PROVENANCE.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(E/'core-asset-fetch.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('R47_ASSET_READY',remote.downloaded,'of',remote.size,time.time()-t,flush=True)
if __name__=='__main__':main()
