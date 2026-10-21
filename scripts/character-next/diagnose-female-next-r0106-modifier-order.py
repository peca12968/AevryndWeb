"""Unsaved causal test: does the bound SurfaceDeform suppress native keys?"""
from pathlib import Path
import bpy,json,time,importlib.util,numpy as np
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0106-native-head-operation';P=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0106-a-native-lid-operation.blend'
sp=importlib.util.spec_from_file_location('r106order',Path(__file__).with_name('build-female-next-r0106-native-lid-operation.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(P));skin=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];u.deliver(0);_,W,_=u.u.b.geom(skin);W=W.copy()
for md in skin.modifiers:md.show_viewport=md.show_render=False
u.deliver(1);_,V,T=u.u.b.geom(skin);view=u.u.v.image('diagnostic-raw-native-closed','face');(E/'modifier-order-causal-test.json').write_text(json.dumps({'source':str(P),'sourceNotSaved':True,'surfaceDeformAndRestCorrectionTemporarilyDisabled':True,'actualRawNativeClosedMaximumMoveM':float(np.linalg.norm(V-W,axis=1).max()),'diagnosticView':view,'notCompleteOperationOrContactAcceptance':True,'seconds':time.time()-tick},indent=2)+'\n',encoding='utf8',newline='\n');print('R106_RAW_CLOSED_DIAGNOSTIC_DONE',time.time()-tick,flush=True)
