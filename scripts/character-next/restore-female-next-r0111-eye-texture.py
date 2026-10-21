"""Restore one required original input from the already archived official zip."""
from pathlib import Path
import hashlib,json,zipfile
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0111-native-mobile-lid-mesh';Z=R/'Reference/character/blender-studio-rain-v3-cc-by4/Rain-v3.3.zip';ARCH=R/'sites-engine-journey/assets-source/aevrynd-character/female-next/source-inputs/r0090-rain-rig/Rain-v3.3.zip';ENTRY='Rain v3.3/textures/TEX-rain_eyes.png';DEST=R/'Reference/character/blender-studio-rain-v3-cc-by4'/ENTRY
def main():
 expected='80217f163f6392dc829233d63c2cfb5e1376775bc34101ad14f39631fea70d24';assert hashlib.sha256(ARCH.read_bytes()).hexdigest()==expected
 if Z.is_file():assert hashlib.sha256(Z.read_bytes()).hexdigest()==expected
 zipSource=Z if Z.is_file() else ARCH
 with zipfile.ZipFile(zipSource) as z:data=z.read(ENTRY)
 if DEST.exists():assert DEST.read_bytes()==data
 else:DEST.parent.mkdir(parents=True,exist_ok=True);DEST.write_bytes(data)
 (E/'restored-source-eye-texture.json').write_text(json.dumps({'officialOriginalZip':str(Z),'alreadyArchivedZip':str(ARCH),'zipSha256':expected,'exactEntry':ENTRY,'restoredFile':str(DEST),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'rights':'Rain Rig (CC) Blender Foundation | studio.blender.org / CC-BY4.0','newDownloadOrInstall':False,'sameCandidateGeometryAndBlendFileUnchanged':True},indent=2)+'\n',encoding='utf8');print('R111_ORIGINAL_EYE_TEXTURE_RESTORED',len(data),flush=True)
if __name__=='__main__':main()
