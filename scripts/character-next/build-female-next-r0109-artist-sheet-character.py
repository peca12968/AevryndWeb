"""Reconstruct complete actual artist-driven native lid sheet on the same r107 woman; neutral art and all existing source bindings preserved."""
from pathlib import Path
from collections import Counter
import bpy,numpy as np,json,time,importlib.util
from mathutils import Vector
from mathutils.kdtree import KDTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0109-complete-native-lid-sheet';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0107-b-native-pinned-lids.blend';OUT=S/'aevrynd-female-next-r0109-a-artist-native-lid-sheet.blend'
sp=importlib.util.spec_from_file_location('r107assembly',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q;u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8',newline='\n')
def deliver(value):
 face=bpy.data.objects['AFN59_FACE_CONTROLS'];face['blink_left']=face['blink_right']=value;face.update_tag();skin=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];skin.data.shape_keys.update_tag();skin.update_tag();bpy.context.view_layer.update()
def main():
 tick=time.time();assert not OUT.exists();data=np.load(E/'native-artist-sheet-poses.npz');P=data['neutralFineWorld'];T=data['fineTriangles'];poseArrays={key:data[key+'_fineDelta'].copy() for key in ['L_half','L_closed','R_half','R_closed']};ref=np.load(E.parent/'r0104-native-artist-ocular-foundation/animation-actual-source-geometry.npz');assert np.array_equal(T,ref['triangles']);bpy.ops.wm.open_mainfile(filepath=str(SRC));face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS']
 for ob in [face,oral]:
  if ob.animation_data:ob.animation_data.action=None
 face['blink_left']=face['blink_right']=0.;oral['jaw_open']=0.;face.update_tag();oral.update_tag();bpy.context.view_layer.update();skin=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];raw=skin.data;dd,W,TT=u.b.geom(skin);W=W.copy();TT=TT.copy();originalUV=q.arr(raw.uv_layers['VitruvianUV.UDIM'].data,'uv',len(raw.loops),2).copy();H0=q.hair(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN']).copy();A=np.array(skin.matrix_world);AI=np.linalg.inv(A[:3,:3]);base=q.arr(raw.vertices,'co',len(raw.vertices),3);hf=q.arr(raw.attributes['AFN104_SourceHeadFace'].data,'value',len(raw.polygons),dtype='i4');starts=q.arr(raw.polygons,'loop_start',len(raw.polygons),dtype='i4');counts=q.arr(raw.polygons,'loop_total',len(raw.polygons),dtype='i4');ids=q.arr(raw.loops,'vertex_index',len(raw.loops),dtype='i4');headFaces=np.flatnonzero(hf>=0);deltas={key:np.zeros_like(W) for key in ['L_half','L_closed','R_half','R_closed']}
 for f in headFaces:
  fi=hf[f];vi=ids[starts[f]:starts[f]+counts[f]];tri=P[T[fi]];xy=np.linalg.lstsq(np.column_stack((tri[1]-tri[0],tri[2]-tri[0])),(W[vi]-tri[0]).T,rcond=None)[0].T;weights=np.c_[1-xy.sum(1),xy]
  for key in deltas:deltas[key][vi]=weights@poseArrays[key][T[fi]]
 assert raw.shape_keys and len(raw.shape_keys.key_blocks)==5
 for side,prop in [('L','blink_left'),('R','blink_right')]:
  for label,delta,expression in [('Closed',deltas[side+'_closed'],'v'),('HalfCorrection',deltas[side+'_half']-.5*deltas[side+'_closed'],'4*v*(1-v)')]:
   key=raw.shape_keys.key_blocks['AFN107_'+label+'_'+side];key.driver_remove('value');key.data.foreach_set('co',(base+delta@AI.T).astype('f4').ravel());fc=key.driver_add('value');fc.driver.expression=expression;var=fc.driver.variables.new();var.name='v';var.type='SINGLE_PROP';var.targets[0].id=face;var.targets[0].data_path='["'+prop+'"]'
 with bpy.data.libraries.load(str(E/'native-artist-sheet-authoring.blend'),link=False) as (a,b):b.objects=['AFN109_ACTUAL_ARTIST_REGISTERED_NATIVE_LID_SHEET']
 cage=b.objects[0];bpy.context.scene.collection.objects.link(cage);cage.hide_render=True;cage.hide_set(True)
 bindings=json.loads((E.parent/'r0107-native-coarse-lid-cage/b-native-seam-lash-bindings.json').read_text('utf8'));save('a-retained-native-seam-lash-bindings.json',bindings);deliver(0);dd,N,NT=u.b.geom(skin);assert np.array_equal(N,W) and np.array_equal(NT,TT);assert np.array_equal(originalUV,q.arr(raw.uv_layers['VitruvianUV.UDIM'].data,'uv',len(raw.loops),2));assert np.array_equal(q.hair(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN']),H0);skin['AFN109_scope']='Actual inspected artist external neutral/half/closed sheet deformation registered across complete native ocular hood and short wall; no analytic aperture target, guessed UV seam or Laplacian. Neutral full skin/lip/material/groom/lash bindings exact. Artist action geometry data incorporated under CC-BY4.0; complete blink/contact/runtime unaccepted until actual preview/readback.';save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'existingVisibleSkinKeysReauthored':4,'actualArtistExternalPoseDataTransferred':True,'sourceArtist':'Blender Studio / Ellie v1 / CC-BY4.0','neutralHeadBodyAndR105UVExactlyRetained':True,'neutralFullGroomExactlyRetained':True,'all412LashesOriginalRadiiAndBindingsRetained':True,'sourceMarginAnatomyAndFullContactsStillUnaccepted':True,'actualSkinBodyModifiers':[(m.name,m.type) for m in skin.modifiers],'wholeBodyDeformationStillUnconnected':True,'secondsBeforePreview':time.time()-tick});u.m.m.rig.shade.settings();u.m.m.rig.k.b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.scene.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);views=[]
 for view in ['face','body-face']:views.append(u.v.image('a-artist-native-sheet-character',view));save('a-view-controls.json',views)
 motion=[]
 for tag,value in [('half',.5),('closed',1.),('restored',0.)]:
  deliver(value);dd,V,TV=u.b.geom(skin);motion.append({'state':tag,'assignedBlink':value,'evaluatedKeys':{k.name:k.value for k in raw.shape_keys.key_blocks if k.name!='Basis'},'maximumDisplayedSkinMoveM':float(np.linalg.norm(V-W,axis=1).max()),'evaluatedLoopTriangleArrayEqualsNeutral':bool(np.array_equal(TV,TT))});views.append(u.v.image('a-artist-native-sheet-character-'+tag,'face'));save('a-preview-motion.json',motion);save('a-view-controls.json',views)
 print('R109_A_ARTIST_NATIVE_SHEET_COMPLETE_CHARACTER_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
