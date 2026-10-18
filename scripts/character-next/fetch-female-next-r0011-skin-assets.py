"""Read only selected CC0 assets from an official ZIP using verified HTTP ranges."""
import io,json,urllib.request,zipfile,hashlib,sys
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0011-skin-brows';E.mkdir(parents=True,exist_ok=True)
URL='https://files.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip'
DEST=R/'engine/assets/characters/female-next/source/textures/makehuman-system-cc0'

class RemoteZip(io.RawIOBase):
    def __init__(self,url):
        self.url=url;self.position=0;self.cache={};self.requests=[]
        with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=25) as r:
            self.size=int(r.headers['Content-Length']);self.etag=r.headers['ETag']
            assert r.headers.get('Accept-Ranges')=='bytes'
    def seekable(self):return True
    def readable(self):return True
    def tell(self):return self.position
    def seek(self,n,whence=0):
        self.position=n if whence==0 else (self.position+n if whence==1 else self.size+n)
        if self.position<0:raise ValueError('negative seek')
        return self.position
    def fetch(self,a,b):
        req=urllib.request.Request(self.url,headers={'Range':f'bytes={a}-{b}','If-Match':self.etag,'User-Agent':'Aevrynd-CC0-asset-research'})
        with urllib.request.urlopen(req,timeout=30) as r:
            assert r.status==206,(r.status,'Server did not honour range; refusing full download')
            assert r.headers['Content-Range']==f'bytes {a}-{b}/{self.size}'
            assert r.headers.get('ETag')==self.etag
            data=r.read(b-a+2);assert len(data)==b-a+1
        self.requests.append({'start':a,'end':b,'bytes':len(data)});return data
    def read(self,n=-1):
        n=self.size-self.position if n<0 else min(n,self.size-self.position)
        if n<=0:return b''
        if n>32*1024*1024:raise ValueError('Unexpected oversized individual read')
        a=self.position;self.position+=n
        if n>=65536:return self.fetch(a,a+n-1)
        first=a//65536;last=(a+n-1)//65536;data=[]
        for block in range(first,last+1):
            if block not in self.cache:self.cache[block]=self.fetch(block*65536,min(self.size-1,(block+1)*65536-1))
            data.append(self.cache[block])
        return b''.join(data)[a-first*65536:a-first*65536+n]

def main():
    remote=RemoteZip(URL);results=[]
    with zipfile.ZipFile(remote) as archive:
        entries=[i for i in archive.infolist() if any(x in i.filename.lower() for x in ('young_asian_female','young_caucasian_female','license','copying','readme'))]
        listing=[{'name':i.filename,'bytes':i.file_size,'compressedBytes':i.compress_size,'crc32':f'{i.CRC:08x}'} for i in entries]
        (E/'official-pack-index.json').write_text(json.dumps({'url':URL,'bytes':remote.size,'etag':remote.etag,'selectedIndex':listing},indent=2)+'\n')
        if '--list' in sys.argv:print(json.dumps(listing,indent=2));return
        for entry in entries:
            name=entry.filename.lower()
            if 'young_asian_female' not in name or name.endswith('/'):continue
            if not name.endswith(('.png','.jpg','.mhmat','.txt','.license')):continue
            if 'female2' in name or 'special_suit' in name:continue
            parts=Path(entry.filename).parts;assert '..' not in parts and not Path(entry.filename).is_absolute()
            data=archive.read(entry) # ZipFile independently checks the decompressed entry CRC32.
            dest=DEST/Path(entry.filename).name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
            results.append({'archiveEntry':entry.filename,'localPath':str(dest),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'zipCrc32':f'{entry.CRC:08x}'})
            print('AFN_R0011_FETCHED='+json.dumps({'name':dest.name,'bytes':len(data)}),flush=True)
    provenance={'sourceURL':URL,'etag':remote.etag,'archiveBytes':remote.size,'license':'CC0-1.0','licenseEvidence':['https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html','https://static.makehumancommunity.org/about/license.html'],'origin':'MakeHuman Community core system graphical assets; do not claim these textures are Aevrynd originals.','codeImported':False,'files':results,'rangeRequests':remote.requests,'totalTransferredBytes':sum(x['bytes'] for x in remote.requests)}
    (E/'download-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');(DEST/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print('AFN_R0011_FETCH_DONE='+str(provenance['totalTransferredBytes']))

if __name__=='__main__':main()
