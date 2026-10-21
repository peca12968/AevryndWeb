"""Measure actual coarse anchor delivery before choosing a structural repair."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0107-native-coarse-lid-cage'
sp=importlib.util.spec_from_file_location('r107anchors',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q;tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(E/'native-coarse-authoring.blend'));ob=bpy.data.objects['AFN107_ORIGINAL_COARSE_LID_AUTHORING_CAGE'];A=np.array(ob.matrix_world);rings=json.loads((E/'actual-native-quad-rings.json').read_text('utf8'));data=np.load(E/'native-coarse-lid-poses.npz');keys=ob.data.shape_keys.key_blocks
for key in keys:key.value=0
for md in ob.modifiers:
 if md.type=='MULTIRES':md.show_viewport=False;md.show_render=False
bpy.context.view_layer.update();_,neutral,T=u.b.geom(ob);neutral=neutral.copy();results={}
for side in ['L','R']:
 key=keys['AFN107_AUTHORING_'+side+'_closed'];key.value=1;ob.data.shape_keys.update_tag();ob.update_tag();bpy.context.view_layer.update();_,actual,TT=u.b.geom(ob);expected=data[side+'_closed_coarseLocal']@A[:3,:3].T+A[:3,3];ids=np.array(rings[side]['rings'][0]);error=np.linalg.norm(actual[ids]-expected[ids],axis=1);results[side]={'actualNativeMarginVertices':ids.tolist(),'desiredMarginMaximumMoveM':float(np.linalg.norm(expected[ids]-neutral[ids],axis=1).max()),'evaluatedMarginMaximumMoveM':float(np.linalg.norm(actual[ids]-neutral[ids],axis=1).max()),'maximumDesiredVersusEvaluatedMarginErrorM':float(error.max()),'medianDesiredVersusEvaluatedMarginErrorM':float(np.median(error))};key.value=0;ob.data.shape_keys.update_tag();ob.update_tag();bpy.context.view_layer.update()
(E/'coarse-anchor-delivery.json').write_text(json.dumps({'source':'native-coarse-authoring.blend','poses':results,'scope':'Actual native coarse data/pose delivery with original Multires temporarily disabled; no complete eyelid appearance/contact proof.','seconds':time.time()-tick},indent=2)+'\n',encoding='utf8',newline='\n');print('R107_COARSE_ANCHOR_DELIVERY_MEASURED',results,flush=True)
