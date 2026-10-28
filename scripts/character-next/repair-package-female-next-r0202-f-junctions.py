from pathlib import Path
import json,ctypes,struct,os,datetime
from ctypes import wintypes as w
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);R=Path(p['directProjectAccess']);E=A/'evidence/character-female-next/r0202-independent-complete-groom'
k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,w.LPVOID,w.DWORD,w.DWORD,w.HANDLE];k.CreateFileW.restype=w.HANDLE;k.DeviceIoControl.argtypes=[w.HANDLE,w.DWORD,w.LPVOID,w.DWORD,w.LPVOID,w.DWORD,ctypes.POINTER(w.DWORD),w.LPVOID];k.DeviceIoControl.restype=w.BOOL;k.CloseHandle.argtypes=[w.HANDLE]
def ioctl(h,code,data):
 inp=ctypes.create_string_buffer(data);out=ctypes.create_string_buffer(16384);done=w.DWORD();ok=k.DeviceIoControl(h,code,inp,len(data),out if code==0x900a8 else None,len(out) if code==0x900a8 else 0,ctypes.byref(done),None)
 if not ok:raise ctypes.WinError(ctypes.get_last_error())
 return out.raw[:done.value]
rows=[]
for link,target in [(R/'engine/assets/characters/female-next/source/r0202-source',A/'assets-source/aevrynd-character/female-next/r0202-source'),(R/'Evidence/character-female-next/r0202-independent-complete-groom',E)]:
 assert str(link).startswith(p['directProjectAccess']+'\\') and target.is_dir();before=None
 try:stat=link.lstat();assert stat.st_file_attributes&0x400
 except FileNotFoundError:os.mkdir(link);stat=None
 handle=k.CreateFileW(str(link),0x40000000,7,None,3,0x02000000|0x00200000,None);assert handle!=w.HANDLE(-1).value
 try:
  if stat is not None:
   before=ioctl(handle,0x900a8,b'');assert struct.unpack_from('<I',before)[0]==0xa0000003;ioctl(handle,0x900ac,struct.pack('<IHH',0xa0000003,0,0))
  sub=('\\??\\'+str(target)[4:]).encode('utf-16-le');pathbuf=sub+b'\0\0\0\0';data=struct.pack('<IHHHHHH',0xa0000003,8+len(pathbuf),0,0,len(sub),len(sub)+2,0)+pathbuf;ioctl(handle,0x900a4,data)
 finally:k.CloseHandle(handle)
 assert os.path.samefile(link,target);rows.append({'link':str(link),'target':str(target),'samefile':True,'previousReparseBytes':before.hex() if before else None})
(E/'f-storage-junction-repair.json').write_text(json.dumps({'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Only new r202 links. PowerShell legacy helper doubled NT prefix on volume GUID target; corrected native substitute name to NT volume path. No C alias writes, historical links/mounts/model bytes changed.','links':rows},indent=2)+'\n',encoding='utf-8')
(E/'package-second-terminal.txt').write_text(Path('F:/AevryndEvidence/CharacterTemp/r202-package-resume.log').read_text('utf-8'),encoding='utf-8')
f=A/'scripts/character-next/resume-package-female-next-r0202.py';raw=f.read_text('utf-8');raw=raw.replace("tail=tail.replace(\"'noAdopt':65", "tail=tail.replace(\"assert not link.exists();subprocess.check_call\",\"assert not link.exists() or os.path.samefile(link,target);\\n if not link.exists():subprocess.check_call\")\ntail=tail.replace(\"'noAdopt':65");f.write_text(raw,encoding='utf-8');print('R202_F_VOLUME_JUNCTIONS_VERIFIED')