"""Fetch only the missing complete original bob01 diffuse/alpha entry.
Bounded4-thread range transfer; retain partial bytes/progress, verify ZIP CRC.
This does not retry r118's timed-out all-five-entry monolithic download.
"""
from pathlib import Path
import json,urllib.request,concurrent.futures,struct,zlib,hashlib,datetime,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0122-native-swept-back-groom';D=Path('C:/Users/USER/AevryndCharacterSources/r0122/native-bob-texture-input');D.mkdir(exist_ok=False);url='https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip';entry=next(x for x in json.loads((R/'Reference/character/makehuman-core-cc0/system-skin/source-pack-central-directory.json').read_text('utf-8')) if x['path']=='hair/bob01/bob01_diffuse.png');start=entry['localOffset'];end=start+30+len(entry['path'].encode())+256+entry['compressed']-1;partdir=D/'verified-range-parts';partdir.mkdir();tick=time.time()
def fetch(pair):
 i,(lo,hi)=pair;req=urllib.request.Request(url,headers={'Range':f'bytes={lo}-{hi}','User-Agent':'Aevrynd-native-hair-texture/1.0'})
 with urllib.request.urlopen(req,timeout=12) as response:
  assert response.status==206 and response.headers['Content-Range']==f'bytes {lo}-{hi}/280737770';data=response.read();assert len(data)==hi-lo+1;headers=dict(response.headers)
 p=partdir/f'{i:03d}.bin';p.write_bytes(data);return {'part':p.name,'start':lo,'end':hi,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'headers':headers}
pairs=list(enumerate((lo,min(lo+131072-1,end)) for lo in range(start,end+1,131072)));records=[]
try:
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  futures=[pool.submit(fetch,p) for p in pairs]
  for f in concurrent.futures.as_completed(futures):records.append(f.result());print('R122_TEXTURE_VERIFIED_RANGE',len(records),'/',len(pairs),flush=True)
 records.sort(key=lambda x:x['start']);data=b''.join((partdir/x['part']).read_bytes() for x in records);h=struct.unpack_from('<IHHHHHIIIHH',data);assert h[0]==0x04034b50;method=h[3];nl,el=h[-2:];assert data[30:30+nl].decode()==entry['path'];payload=data[30+nl+el:30+nl+el+entry['compressed']];assert len(payload)==entry['compressed'];full=zlib.decompress(payload,-15) if method==8 else payload;assert len(full)==entry['uncompressed'] and zlib.crc32(full)&0xffffffff==entry['crc32'];(D/'bob01_diffuse.png').write_bytes(full)
 record={'status':'COMPLETE_ORIGINAL_RGBA_ENTRY_CRC_AND_SIZE_VERIFIED','url':url,'entry':entry,'fullBytes':len(full),'fullSha256':hashlib.sha256(full).hexdigest(),'maxNetworkThreads':4,'requests':records,'originalRangePartsRetained':True,'license':'MakeHuman system assets CC0; original geometry/MHMAT notices/license/provenance reused','seconds':time.time()-tick,'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()};(D/'PROVENANCE.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');(E/'native-bob-texture-fetch.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print('R122_COMPLETE_NATIVE_BOB_TEXTURE_READY',len(full),flush=True)
except Exception as exc:
 (E/'native-bob-texture-fetch-failure.json').write_text(json.dumps({'error':repr(exc),'retainedCompletedRanges':records,'seconds':time.time()-tick,'entry':entry},indent=2)+'\n',encoding='utf-8');raise
