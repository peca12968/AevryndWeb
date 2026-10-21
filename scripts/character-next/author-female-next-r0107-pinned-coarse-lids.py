"""Retain the native sculpted hood but enforce actual margin/outer anchors.

Delivery evidence shows the soft coarse result misses its requested margin by
6.8mm. This changes the constraint construction, not its amplitude/iterations.
"""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0107-native-coarse-lid-cage'
sp=importlib.util.spec_from_file_location('r107pin',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q
def main():
 tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(E/'native-coarse-authoring.blend'));source=bpy.data.objects['AFN107_ORIGINAL_COARSE_LID_AUTHORING_CAGE'];data=np.load(E/'native-coarse-lid-poses.npz');rings=json.loads((E/'actual-native-quad-rings.json').read_text('utf8'));info=json.loads((E/'coarse-authoring.json').read_text('utf8'));anchors=np.array(info['fixedAnchorVertices'],int);local=data['neutralCoarseLocal'];keys=source.data.shape_keys.key_blocks
 for k in keys:k.value=0
 for md in source.modifiers:
  if md.type=='MULTIRES':md.show_viewport=md.show_render=False
 pin=source.copy();pin.data=source.data.copy();pin.shape_key_clear();pin.name='AFN107_CONSTRAINED_NATIVE_COARSE_LID_CAGE';bpy.context.scene.collection.objects.link(pin)
 for md in list(pin.modifiers):
  if md.type=='LAPLACIANDEFORM':pin.modifiers.remove(md)
  elif md.type=='MULTIRES':md.show_viewport=md.show_render=True;md.levels=md.render_levels=1
 pin.data.vertices.foreach_set('co',local.astype('f4').ravel());pin.data.update();pin.update_tag();bpy.context.view_layer.update();dd,V0,T=u.b.geom(pin);V0=V0.copy();T=T.copy();arrays={'neutralFineWorld':V0,'fineTriangles':T,'neutralCoarseLocal':local};report={}
 for side in ['L','R']:
  margin=np.array(rings[side]['rings'][0],int)
  for label in ['half','closed']:
   key=keys['AFN107_AUTHORING_'+side+'_'+label];key.value=1;source.data.shape_keys.update_tag();source.update_tag();bpy.context.view_layer.update();sd,soft,st=u.b.geom(source);soft=q.arr(sd.vertices,'co',len(sd.vertices),3).copy();assert len(soft)==len(local);target=data[side+'_'+label+'_coarseLocal'].astype('f4');soft[anchors]=local[anchors].astype('f4');soft[margin]=target[margin];assert np.array_equal(soft[margin],target[margin]);assert np.array_equal(soft[np.setdiff1d(anchors,margin)],local[np.setdiff1d(anchors,margin)].astype('f4'));pin.data.vertices.foreach_set('co',soft.astype('f4').ravel());pin.data.update();pin.update_tag();bpy.context.view_layer.update();dd,V,TT=u.b.geom(pin);assert len(V)==len(V0);arrays[side+'_'+label+'_fineDelta']=V-V0;arrays[side+'_'+label+'_coarseLocal']=soft;report[side+'_'+label]={'actualFineMaximumMoveM':float(np.linalg.norm(V-V0,axis=1).max()),'all20CoarseMarginTargetsDeliveredExactlyAsStoredFloat32':True,'outsideOrbitalAnchorsExactlyRestoredAsStoredFloat32':True,'evaluatedFineTriangleArrayEqualsNeutral':bool(np.array_equal(TT,T)),'scope':'Exact source-coarse constraints; fine anatomy/contact and rendered full blink still require actual preview.'};key.value=0;source.data.shape_keys.update_tag();source.update_tag();bpy.context.view_layer.update()
 pin.data.vertices.foreach_set('co',local.astype('f4').ravel());pin.data.update();pin.update_tag();pin.shape_key_add(name='Basis')
 for side in ['L','R']:
  for label in ['half','closed']:pin.shape_key_add(name='AFN107_PINNED_AUTHORING_'+side+'_'+label).data.foreach_set('co',arrays[side+'_'+label+'_coarseLocal'].astype('f4').ravel())
 pin.hide_render=True;pin['scope']='Native quad hood with exact coarse margin/outer anchors. Baked original Multires poses; no soft Laplacian modifier left on this delivered authoring cage. Not a finite-contact or natural-blink certificate.';source.hide_render=True;np.savez_compressed(E/'native-coarse-lid-poses-pinned.npz',**arrays);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(E/'native-coarse-authoring-pinned.blend'),compress=True);(E/'pinned-coarse-authoring.json').write_text(json.dumps({'construction':'Retain actual native quad hood deformation, then impose exact original20 margin targets and fixed outer orbital coordinates before original Multires evaluation. Deliver sculpted coarse poses with only original Multires, not a soft solver in the final cage. No angle, radius, clearance, weight or iteration change.','newEvidence':'coarse-anchor-delivery.json: requested11.31mm but delivered4.48mm, margin misses6.83/6.86mm.','poses':report,'seconds':time.time()-tick},indent=2)+'\n',encoding='utf8',newline='\n');print('R107_ACTUAL_PINNED_COARSE_POSES_AUTHORED',time.time()-tick,flush=True)
if __name__=='__main__':main()
