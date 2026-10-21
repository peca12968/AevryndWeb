"""One unsaved full-character test: original Multires versus actual visible rim.

Also record the existing native quad rows as geometry evidence, not anatomy
labels inferred merely from a UV seam. No candidate is saved here.
"""
from pathlib import Path
from collections import defaultdict
import bpy,numpy as np,json,time,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0108-visible-eyelid-rim';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r108source',Path(__file__).with_name('build-female-next-r0107-pinned-character.py'));b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b);u=b.u;q=u.q;u.v.E=E
def graph(d):return [tuple(map(int,p.vertices)) for p in d.polygons]
def main():
 tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0107-b-native-pinned-lids.blend'));cage=bpy.data.objects['AFN107_CONSTRAINED_NATIVE_COARSE_LID_CAGE'];keys=cage.data.shape_keys.key_blocks
 for k in keys:k.value=0
 bpy.context.view_layer.update();d,P0,T0=u.b.geom(cage);P0=P0.copy();T0=T0.copy();polys=graph(d);uv=q.arr(d.uv_layers['UVMap'].data,'uv',len(d.loops),2).copy();starts=q.arr(d.polygons,'loop_start',len(d.polygons),dtype='i4');counts=q.arr(d.polygons,'loop_total',len(d.polygons),dtype='i4');front=[]
 for fi,(s,n) in enumerate(zip(starts,counts)):
  x=uv[s:s+n]
  if np.all((x[:,0]>.2)&(x[:,0]<.8)&(x[:,1]>.5)):front.append(fi)
 edges=defaultdict(list)
 for f in front:
  poly=polys[f]
  for a,z in zip(poly,poly[1:]+poly[:1]):edges[tuple(sorted((a,z)))].append(f)
 rings={}
 for side,sign in [('L',1),('R',-1)]:
  adj=defaultdict(list)
  for edge,faces in edges.items():
   pts=P0[list(edge)]
   if len(faces)==1 and np.all((pts[:,2]>1.44)&(pts[:,2]<1.485)&(pts[:,0]*sign>.008)&(pts[:,0]*sign<.055)&(pts[:,1]<-.10)):adj[edge[0]].append(edge[1]);adj[edge[1]].append(edge[0])
  first=min(adj,key=lambda i:P0[i,0]);loop=[first,adj[first][0]]
  while loop[-1]!=first:loop.append(next(i for i in adj[loop[-1]] if i!=loop[-2]))
  rows=[loop[:-1]];used=set()
  for step in range(4):
   mapping={};facesUsed=[];valid=True
   for a,z in zip(rows[-1],np.roll(rows[-1],-1)):
    matches=[f for f in edges[tuple(sorted((int(a),int(z))))] if f not in used]
    if len(matches)!=1:valid=False;break
    f=matches[0];poly=list(polys[f]);facesUsed.append(f)
    if len(poly)!=4:valid=False;break
    for i,j in [(a,z),(z,a)]:
     k=poly.index(i);other=next(x for x in [poly[(k-1)%4],poly[(k+1)%4]] if x!=j)
     if i in mapping and mapping[i]!=other:valid=False;break
     mapping[i]=other
    if not valid:break
   if not valid:break
   nxt=[int(mapping[i]) for i in rows[-1]]
   if len(set(nxt))!=len(nxt):break
   rows.append(nxt);used.update(facesUsed)
  rings[side]={'nativeRows':rows,'neutralWorldRows':[P0[row].tolist() for row in rows],'anatomicalVisibleMarginNotAssumedFromUVSeam':True}
 for side in ['L','R']:keys['AFN107_PINNED_AUTHORING_'+side+'_closed'].value=1
 cage.data.shape_keys.update_tag();cage.update_tag();bpy.context.view_layer.update();dd,PM,TM=u.b.geom(cage);PM=PM.copy();smooth=cage.copy();smooth.data=cage.data.copy();bpy.context.scene.collection.objects.link(smooth);smooth.name='AFN108_UNSAVED_NO_ORIGINAL_MULTIRES_DIAGNOSTIC'
 for md in list(smooth.modifiers):
  if md.type=='MULTIRES':smooth.modifiers.remove(md)
 sub=smooth.modifiers.new('AFN108_DIAGNOSTIC_SUBSURF_ONLY','SUBSURF');sub.levels=sub.render_levels=1;smooth.hide_render=True;bpy.context.view_layer.update();sd,PS,TS=u.b.geom(smooth);PS=PS.copy();assert len(PS)==len(P0) and graph(sd)==polys,'No verified native vertex/face correspondence; do not transfer a guess'
 skin=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];b.deliver(0)
 for fc in skin.data.shape_keys.animation_data.drivers:fc.mute=True
 for key in skin.data.shape_keys.key_blocks:key.value=0
 raw=skin.data;A=np.array(skin.matrix_world);AI=np.linalg.inv(A[:3,:3]);base=q.arr(raw.vertices,'co',len(raw.vertices),3);W=base@A[:3,:3].T+A[:3,3];hf=q.arr(raw.attributes['AFN104_SourceHeadFace'].data,'value',len(raw.polygons),dtype='i4');st=q.arr(raw.polygons,'loop_start',len(raw.polygons),dtype='i4');cnt=q.arr(raw.polygons,'loop_total',len(raw.polygons),dtype='i4');ids=q.arr(raw.loops,'vertex_index',len(raw.loops),dtype='i4');delta=np.zeros_like(W)
 for face in np.flatnonzero(hf>=0):
  f=hf[face];vi=ids[st[face]:st[face]+cnt[face]];tri=P0[T0[f]];xy=np.linalg.lstsq(np.column_stack((tri[1]-tri[0],tri[2]-tri[0])),(W[vi]-tri[0]).T,rcond=None)[0].T;weights=np.c_[1-xy.sum(1),xy];delta[vi]=weights@(PS-P0)[T0[f]]
 key=skin.shape_key_add(name='AFN108_UNSAVED_DIAGNOSTIC_CLOSED_NO_SCULPT');key.data.foreach_set('co',(base+delta@AI.T).astype('f4').ravel());key.value=1;skin.data.shape_keys.update_tag();skin.update_tag();bpy.context.view_layer.update();view=u.v.image('diagnostic-closed-without-original-Multires','face');np.savez_compressed(E/'native-visible-rim-diagnostic.npz',neutralFineWorld=P0,originalMultiresClosedWorld=PM,smoothSubsurfClosedWorld=PS,triangles=T0);report={'source':str(S/'aevrynd-female-next-r0107-b-native-pinned-lids.blend'),'sourceNotSaved':True,'nativeQuadRows':rings,'originalClosedVersusNoSculptMaximumWorldDifferenceM':float(np.linalg.norm(PM-PS,axis=1).max()),'nativeVertexAndPolygonCorrespondenceVerified':True,'actualFullCharacterDiagnosticView':view,'scope':'Original captured Multires detail removed only in the unsaved closed geometry diagnostic. Lighting, skin shader/textures and optics unchanged. Not an adopted candidate, anatomical boundary or contact proof.','seconds':time.time()-tick};(E/'visible-rim-causal-diagnostic.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('R108_ACTUAL_VISIBLE_RIM_DIAGNOSTIC_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
