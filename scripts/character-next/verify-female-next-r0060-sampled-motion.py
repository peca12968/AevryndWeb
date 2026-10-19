"""Actual extra poses after endpoint success; never call sampling continuous."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
sp=importlib.util.spec_from_file_location('scope60',Path(__file__).with_name('verify-female-next-r0060-assembly.py'));k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
E=k.E
def main():
    tick=time.time();build=k.read(E/'b-build-summary.json');end=k.read(E/'b-contact-verification.json');assert end['status']=='PASS_TWO_ENDPOINT_SURFACE_SCOPE_ONLY';source=Path(build['output']);assert k.b.sha(source)==build['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(source));parts=[bpy.data.objects[build['visibleComponents'][str(i)]] for i in range(5)];ctrl=bpy.data.objects['AFN59_FACE_CONTROLS'];ctrl.animation_data.action=None
    for obj in parts:
        for md in obj.modifiers:
            if md.type=='SUBSURF':md.levels=md.render_levels
    def set_controls(left,right):ctrl['blink_left']=left;ctrl['blink_right']=right;ctrl.update_tag();bpy.context.view_layer.update()
    set_controls(0,0);V0,T0,mi0,f0=k.join([k.mesh(o) for o in parts]);set_controls(1,1);V1,T1,mi1,f1=k.join([k.mesh(o) for o in parts]);affected=np.linalg.norm(V1-V0,axis=1)>1e-9;caps=set(i for row in build['nativeInteriorCorrections'].values() for i in row['originalPatchFaces'])
    for T,fi in ((T0,f0),(T1,f1)):affected[np.unique(T[np.isin(fi,list(caps))])]=True
    result={'source':str(source),'sourceSha256':build['outputSha256'],'status':'RUNNING','poses':{},'scope':'Actual render-level sampled surface tests after qualified endpoints; no continuous proof or facial-hair/whole-body self inference.'};k.save('b-additional-pose-verification.json',result)
    for label,left,right in [('quarter',.25,.25),('half',.5,.5),('threeQuarter',.75,.75),('leftWink',1.,0.),('rightWink',0.,1.)]:
        set_controls(left,right);V,T,mi,fi=k.join([k.mesh(o) for o in parts]);row=k.contacts(V,T,mi,fi,affected);row['controls']=[left,right]
        if left==right:row['maximumSourceAffinePositionResidualM']=float(np.linalg.norm(V-(V0+left*(V1-V0)),axis=1).max())
        result['poses'][label]=row;k.save('b-additional-pose-verification.json',result);print('R60_ADDITIONAL_POSE',label,row['status'],row['actualNonAdjacentSelfPairs'],{n:x['unqualifiedPairs'] for n,x in row['completeInterfaces'].items()},flush=True)
        if row['status']!='PASS_TESTED_ENDPOINT_SURFACE_SCOPE':result['status']='FAIL_INTERMEDIATE_OR_WINK_STOP_EXPANSION';break
    else:result['status']='PASS_SEVEN_TESTED_STATIC_POSES_ONLY'
    result['continuousMotionFacialHairFiniteSelfAndRuntime']='NOT_ACCEPTED';result['seconds']=time.time()-tick;k.save('b-additional-pose-verification.json',result);print('R60_MOTION_SAMPLE_SCOPE',result['status'],time.time()-tick,flush=True)
if __name__=='__main__':main()
