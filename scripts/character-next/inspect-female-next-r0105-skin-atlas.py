"""Read-only source texture inspection, not a new skin asset."""
from pathlib import Path
import bpy,numpy as np
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0105-native-head-skin-chart';P=R/'engine/assets/characters/female-next/source/study-vitruvian-textures/Light_Skin_Color.1001.exr';im=bpy.data.images.load(str(P));w,h=im.size;pix=np.empty(w*h*4,'f4');im.pixels.foreach_get(pix);pix=pix.reshape(h,w,4);np.savez_compressed(E/'source-skin-colour-inspection.npz',pixels=pix[::4,::4]);preview=bpy.data.images.new('AFN105_READ_ONLY_ATLAS_REFERENCE',width=w//4,height=h//4);preview.pixels.foreach_set(pix[::4,::4].ravel());preview.file_format='PNG';preview.filepath_raw=str(E/'source-skin-atlas-reference.png');preview.save();print('R105_ATLAS_INSPECT_DONE',w,h,flush=True)
