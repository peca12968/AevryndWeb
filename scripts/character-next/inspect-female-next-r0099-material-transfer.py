from pathlib import Path
import bpy,json,numpy as np,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0099-continuous-head-neck';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r99mat',Path(__file__).with_name('build-female-next-r0099-continuous-skin.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);q=m.q
bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0099-a-continuous-head-neck.blend'));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();out={}
for key,name in [('skin','AFN74_SKIN_AND_EXISTING_OCULAR_LINING'),('head','AFN98_ORIGINAL_ARTIST_HEAD_AND_NECK_COLLAR'),('joined','AFN99_CONTINUOUS_RENDER_SKIN')]:
 ob=bpy.data.objects[name];d,V=q.geom(ob);d.calc_loop_triangles();mi=q.arr(d.polygons,'material_index',len(d.polygons),dtype='i4');out[key]={'slots':[(x.name if x else None) for x in d.materials],'usedSlots':dict(zip(*[a.tolist() for a in np.unique(mi,return_counts=True)])),'UV':[{'name':x.name,'bounds':[q.arr(x.data,'uv',len(d.loops),2).min(0).tolist(),q.arr(x.data,'uv',len(d.loops),2).max(0).tolist()]} for x in d.uv_layers]}
 if key=='joined':out[key]['lastHeadPolygonsMaterialIDs']=mi[659328:659350].tolist()
out['originalHeadFirstMaterialIDs']=np.load(E/'actual-interface-input.npz')['headMaterial'][:22].tolist();(E/'material-transfer-inspection.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2),flush=True)
