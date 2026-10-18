"""Inspect existing native hair authoring data and actual head bounds."""
import bpy,json
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0012-layered-hair';E.mkdir(parents=True,exist_ok=True)
REF=R/'sites-engine-journey/assets-source/reference/cc0/makehuman-haireditor/unpacked/hair/haireditor/hair.blend'
with bpy.data.libraries.load(str(REF),link=False) as (data_from,data_to): reference={'objects':list(data_from.objects),'nodeGroups':list(data_from.node_groups),'materials':list(data_from.materials)}
bpy.ops.wm.open_mainfile(filepath=str(R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0011-b-ridge-skin-brows-study.blend'))
b=bpy.data.objects['AFN_R0008_Body'];p=[v.co for v in b.data.vertices if v.co.z>1.40];raw=bpy.data.objects['AFN_R0005_EditableNativeCC0'];g=raw.vertex_groups.get('helper-hair')
result={'referenceFile':str(REF),'reference':reference,'headBounds':[[min(v[a] for v in p),max(v[a] for v in p)] for a in range(3)],'nativeScalpHelperVertices':sum(any(x.group==g.index for x in v.groups) for v in raw.data.vertices) if g else None,'curveDataSupportsHairCurves':hasattr(bpy.data,'hair_curves')}
(E/'hair-authoring-inspection.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
