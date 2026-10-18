"""Read only an official CC0 archive directory for the next oral-layer task."""
import json,zipfile,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('fetch',Path(__file__).with_name('fetch-female-next-r0011-skin-assets.py'));fetch=importlib.util.module_from_spec(spec);spec.loader.exec_module(fetch)
def main():
    remote=fetch.RemoteZip(fetch.URL)
    with zipfile.ZipFile(remote) as archive:
        entries=[{'path':i.filename,'bytes':i.file_size,'compressedBytes':i.compress_size,'crc32':f'{i.CRC:08x}'} for i in archive.infolist() if any(word in i.filename.lower() for word in ('teeth','tongue','tooth')) and i.filename.lower().endswith(('.obj','.mhclo','.mhmat','.json','.license','.txt'))]
    dest=fetch.R/'Evidence/character-female-next/r0023-neutral-mouth/next-oral-assets-index.json';dest.write_text(json.dumps({'officialArchiveURL':fetch.URL,'archiveBytes':remote.size,'etag':remote.etag,'entries':entries,'rangeRequests':remote.requests,'totalTransferredBytes':sum(x['bytes'] for x in remote.requests),'scope':'Archive directory only; no mesh assets downloaded or adopted in this round. Verify per-entry author/license metadata before future integration.'},indent=2)+'\n',encoding='utf8');print(json.dumps({'entries':len(entries),'names':[e['path'] for e in entries],'bytesTransferred':sum(x['bytes'] for x in remote.requests)},indent=2))
if __name__=='__main__':main()
