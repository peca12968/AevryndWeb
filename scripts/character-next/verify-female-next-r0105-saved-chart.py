"""Independent saved readback of the scoped UV edit; no new collision claim."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0105-native-head-skin-chart';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r105verify',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def hasharray(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def material(m):
 rows=[]
 for n in m.node_tree.nodes:
  ins=[]
  for s in n.inputs:
   val=None
   if hasattr(s,'default_value'):
    val=s.default_value
    try:val=list(val)
    except TypeError:pass
    if not isinstance(val,(str,int,float,bool,list,type(None))):val=repr(val)
   ins.append([s.identifier,val,[[l.from_node.name,l.from_socket.identifier] for l in s.links]])
  rows.append({'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'blend':getattr(n,'blend_type',None),'uv':getattr(n,'uv_map',None),'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None,'inputs':ins})
 return hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
def snapshot(p):
 bpy.ops.wm.open_mainfile(filepath=str(p));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];d,V,T=u.b.geom(skin);V=V.copy();T=T.copy();uv=q.arr(d.uv_layers['VitruvianUV.UDIM'].data,'uv',len(d.loops),2);out={'source':str(p),'sourceBytes':p.stat().st_size,'sourceSha256':sha(p),'vertices':len(V),'triangles':len(T),'worldVertexSha256':hasharray(V),'triangleSha256':hasharray(T),'materialIndexSha256':hasharray(q.arr(d.polygons,'material_index',len(d.polygons),dtype='i4')),'canonicalUVSha256':hasharray(uv),'allUVFinite':bool(np.isfinite(uv).all()),'skinModifiers':[(m.name,m.type) for m in skin.modifiers],'skinMaterialGraphSha256':material(skin.data.materials[4]),'groomWorldSha256':hasharray(q.hair(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'])),'lashWorldSha256':hasharray(q.hair(bpy.data.objects['AFN57_NATIVE_LASHES'])),'optics':{},'externalTextures':[]}
 for name in ['AFN104_NATIVE_L_SCLERA','AFN104_NATIVE_R_SCLERA','AFN104_NATIVE_L_IRIS','AFN104_NATIVE_R_IRIS']:
  dd,P,TT=u.b.geom(bpy.data.objects[name]);out['optics'][name]={'vertices':hasharray(P),'triangles':hasharray(TT)}
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath:
   path=Path(bpy.path.abspath(im.filepath));assert path.is_file(),str(path);out['externalTextures'].append({'name':im.name,'relative':im.filepath,'sha256':sha(path),'bytes':path.stat().st_size})
 out['externalTextures'].sort(key=lambda x:x['name']);return out
def main():
 tick=time.time();a=snapshot(S/'aevrynd-female-next-r0104-b2-native-head-material-repair.blend');b=snapshot(S/'aevrynd-female-next-r0105-a-native-lip-chart.blend');keys=['vertices','triangles','worldVertexSha256','triangleSha256','materialIndexSha256','skinModifiers','skinMaterialGraphSha256','groomWorldSha256','lashWorldSha256','optics','externalTextures'];assert all(a[k]==b[k] for k in keys);assert a['canonicalUVSha256']!=b['canonicalUVSha256'] and b['allUVFinite'];row={'baseline':a,'candidate':b,'exactlyUnchangedFields':keys,'status':'PASS_INDEPENDENT_REOPEN_SCOPED_CHART_EDIT_ONLY','newSkinStillStatic':True,'inheritedContactFailure':{'evidence':str(E.parent/'r0104-native-artist-ocular-foundation/minimum-saved-readback.json'),'scope':'Actual neutral skin/paired optics geometry byte signatures match B2. Its existing witnesses remain applicable; this is not a new full collision audit.','candidatePairsL':284,'candidatePairsR':311,'storedIntersectionOrTouchWitnessesPerSide':16,'globalSignedMinimumM':None,'continuousFiniteHairSelfClothAccepted':False},'runtimeAccepted':False,'seconds':time.time()-tick};(E/'independent-saved-chart-readback.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf8',newline='\n');print('R105_SAVED_CHART_VERIFIED',time.time()-tick,flush=True)
if __name__=='__main__':main()
