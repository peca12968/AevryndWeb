"""Reopen/lineage verification only for visually rejected complete styles.
Does not spend full-groom contact cost on failed appearance.
"""
import bpy,importlib.util,time,json
from pathlib import Path
import numpy as np
sp=importlib.util.spec_from_file_location('crop46v',Path(__file__).with_name('build-female-next-r0046-textured-crop.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
b=a.b;v=a.v;f=a.f;E=a.E;S=a.S
def main():
    tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(a.SRC));before=f.state();oldP,oldR=v.hair_arrays(bpy.data.objects['AFN33_C_BODY_BOUND_FIBRES']);rows=[]
    for tag,path,folder in [('A',a.OUT,E),('B',S/'aevrynd-female-next-r0046-b-explicit-tuft-crop.blend',E/'b-explicit-tufts')]:
        summary=json.loads((folder/'a-build-summary.json').read_text());assert b.sha(path)==summary['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(path));hair=bpy.data.objects['AFN33_C_BODY_BOUND_FIBRES'];P,R=v.hair_arrays(hair);ep,er=a.live.eval_arrays(hair);state=f.state();assert state['meshes']==before['meshes'] and state['materials']==before['materials'] and state['skinFields']==before['skinFields'] and state['stage']==before['stage'];assert all(state['curves'][n]==s for n,s in before['curves'].items() if n!=hair.name);assert np.array_equal(P[:,0],oldP[:,0]) and np.array_equal(R,oldR) and np.array_equal(P,ep) and np.array_equal(R,er);cache=np.load(folder/'a-complete-paths.npz');mx=np.array(hair.matrix_world);world=P.astype('f8')@mx[:3,:3].T+mx[:3,3];err=float(np.linalg.norm(world-cache['positionsWorld'],axis=2).max());assert err<2e-7;assert np.isfinite(P).all() and len(P)==12000 and P.shape[1]==128
        roots=world[:,0];rows.append({'tag':tag,'source':str(path),'sourceSha256':b.sha(path),'sourceBytes':path.stat().st_size,'reopened':True,'allUnrelatedVisibleMeshesSkinMaterialsStageExact':True,'all12000RootsAndNativeRadiiExact':True,'liveGuideRestZeroExact':True,'currentCurveCacheReadbackErrorMaxM':err,'curves':12000,'points':1536000,'rootCoverageWorldBoundsM':[roots.min(0).tolist(),roots.max(0).tolist()],'rootsBelowZ1_47':int((roots[:,2]<1.47).sum()),'fullGroomContacts':'NOT_RUN_VISUALLY_REJECTED','scope':'Exact saved editable complete static style data, not appearance/physics/engine acceptance'})
    a.save('rejected-grooms-reopen-verification.json',{'status':'PASS_REOPENED_EXACT_STYLE_DATA_NOT_CHARACTER_ACCEPTANCE','rows':rows,'seconds':time.time()-tick});print('R46_REOPENED_REJECTED',time.time()-tick,flush=True)
if __name__=='__main__':main()
