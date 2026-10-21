"""Extract only complete used native hair entries, with exact range/header/CRC/size verification."""
from pathlib import Path
import json,urllib.request,struct,zlib,hashlib,datetime
R=Path('D:/Download/Aevrynd');D=R/'Reference/character/makehuman-core-cc0/system-bob01-geometry-first';D.mkdir(exist_ok=False)
rows=json.loads((D.parent/'system-skin/source-pack-central-directory.json').read_text(encoding='utf-8'))
index={x['path']:x for x in rows};url='https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip'
groups=[['hair/bob01/bob01.thumb','hair/bob01/bob01.mhclo','hair/bob01/bob01.mhmat'],['hair/bob01/bob01.obj']];records=[];requests=[]
for paths in groups:
    start=min(index[p]['localOffset'] for p in paths);end=max(index[p]['localOffset']+30+len(p.encode())+256+index[p]['compressed'] for p in paths)
    request=urllib.request.Request(url,headers={'Range':f'bytes={start}-{end}','User-Agent':'Aevrynd-character-asset-research/1.0'})
    with urllib.request.urlopen(request,timeout=60) as response:
        assert response.status==206;contentRange=response.headers['Content-Range'];assert contentRange==f'bytes {start}-{end}/280737770';data=response.read();assert len(data)==end-start+1;headers=dict(response.headers)
    requests.append({'range':[start,end],'headers':headers,'receivedBytes':len(data)})
    for path in paths:
        row=index[path];offset=row['localOffset']-start;header=struct.unpack_from('<IHHHHHIIIHH',data,offset);assert header[0]==0x04034b50;method=header[3];nameLength,extraLength=header[-2:];name=data[offset+30:offset+30+nameLength].decode('utf-8');assert name==path and method==row['method'];payload=data[offset+30+nameLength+extraLength:offset+30+nameLength+extraLength+row['compressed']];assert len(payload)==row['compressed'];full=zlib.decompress(payload,-15) if method==8 else payload;assert len(full)==row['uncompressed'] and zlib.crc32(full)&0xffffffff==row['crc32'];dest=D/Path(path).name;dest.write_bytes(full);records.append(row|{'file':dest.name,'sha256':hashlib.sha256(full).hexdigest(),'bytes':len(full)});print('R118_FULL_ASSET',path,len(full),flush=True)
(D/'PROVENANCE.json').write_text(json.dumps({'sourcePack':url,'sourcePackTotalBytes':280737770,'officialLicensePage':'https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html','license':'CC0','author':'makehuman_system / MakeHuman Team','licenseOriginalRetained':'../LICENSE.ASSETS.md','completeSelectedUsedEntriesOnly':True,'fullZipNotDownloadedOrClaimed':True,'requests':requests,'files':records,'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n',encoding='utf-8');print('R118_GEOMETRY_FIRST_COMPLETE',flush=True)
