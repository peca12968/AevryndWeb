"""Rebuild disposable scene-linear sampling cache from unchanged CC0 PNG."""
from pathlib import Path
from PIL import Image
import hashlib,numpy as np
R=Path(r'D:\Download\Aevrynd');source=R/'engine/assets/characters/female-next/source/textures/makehuman-system-cc0/young_lightskinned_female_diffuse3.png';fallback=R/'sites-engine-journey/assets-source/aevrynd-character/female-next/textures/makehuman-system-cc0/young_lightskinned_female_diffuse3.png'
if not source.exists():source=fallback
assert hashlib.sha256(source.read_bytes()).hexdigest()=='1d82f782b7d2da732229633bd2d14754d873fff53cdb1d088977bcf67ae19dde'
output=R/'Evidence/character-female-next/r0049-skin-response/body-atlas-linear-cache.npz';output.parent.mkdir(parents=True,exist_ok=True);s=np.array(Image.open(source).convert('RGB'),dtype='f4')/255;rgb=np.where(s<=.04045,s/12.92,((s+.055)/1.055)**2.4);np.savez_compressed(output,rgb=rgb);print('R49_LINEAR_CACHE_REBUILT',rgb.shape)
