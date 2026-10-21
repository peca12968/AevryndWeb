"""Inspect native artist chart and actual original skin lip correspondence."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0105-native-head-skin-chart'; P=R/'Reference/character/blender-human-base-meshes-v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend'
sp=importlib.util.spec_from_file_location('r105inspect',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q
bpy.ops.wm.open_mainfile(filepath=str(R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0104-b2-native-head-material-repair.blend'))
arrays={};report={}
for tag,name in [('current','AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'),('original','AFN99_ORIGINAL_CONTINUOUS_ARTIST_SKIN')]:
 ob=bpy.data.objects[name];d,W,T=u.b.geom(ob);d.calc_loop_triangles();loops=q.arr(d.loop_triangles,'loops',len(T),3,dtype='i4');cent=W[T].mean(1);sel=np.flatnonzero((cent[:,2]>1.345)&(cent[:,2]<1.43)&(abs(cent[:,0])<.065)&(cent[:,1]<-.045));arrays[tag+'World']=W[T[sel]];arrays[tag+'UV']=q.arr(d.uv_layers['VitruvianUV.UDIM'].data,'uv',len(d.loops),2)[loops[sel]];arrays[tag+'Material']=q.arr(d.polygons,'material_index',len(d.polygons),dtype='i4')[q.arr(d.loop_triangles,'polygon_index',len(T),dtype='i4')[sel]];report[tag]={'triangles':len(sel),'uvLayers':[x.name for x in d.uv_layers],'bounds':[arrays[tag+'World'].min((0,1)).tolist(),arrays[tag+'World'].max((0,1)).tolist()]}
 for layer in d.uv_layers:arrays[tag+'UV-'+layer.name]=q.arr(layer.data,'uv',len(d.loops),2)[loops[sel]]
with bpy.data.libraries.load(str(P),link=False) as (a,b):b.objects=['GEO-head_animation_realistic']
ob=b.objects[0];bpy.context.scene.collection.objects.link(ob);bpy.context.view_layer.update();d,W,T=u.b.geom(ob);d.calc_loop_triangles();loops=q.arr(d.loop_triangles,'loops',len(T),3,dtype='i4');arrays['nativeLocal']=q.arr(d.vertices,'co',len(d.vertices),3);arrays['nativeTriangles']=T;report['native']={'uvLayers':[x.name for x in d.uv_layers],'vertices':len(W),'triangles':len(T),'materials':[m.name if m else None for m in d.materials]}
for layer in d.uv_layers:arrays['nativeUV-'+layer.name]=q.arr(layer.data,'uv',len(d.loops),2)[loops]
np.savez_compressed(E/'actual-lip-and-native-chart.npz',**arrays);(E/'native-chart-inspection.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('R105_CHART_INSPECTION_DONE',report,flush=True)
