"""Check repaired tissue topology and ocular-space containment explicitly."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
from mathutils import Vector
sp=importlib.util.spec_from_file_location('volume60',Path(__file__).with_name('verify-female-next-r0060-assembly.py'));k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
E=k.E
def edges(T):
    ed=np.sort(np.concatenate((T[:,[0,1]],T[:,[1,2]],T[:,[2,0]])),axis=1);_,counts=np.unique(ed,axis=0,return_counts=True);return {'boundaryEdges':int((counts==1).sum()),'nonManifoldEdges':int((counts>2).sum())}
def main():
    tick=time.time();a=k.read(E/'b-build-summary.json');assert k.b.sha(Path(a['output']))==a['outputSha256'];bpy.ops.wm.open_mainfile(filepath=a['output']);body=bpy.data.objects[a['visibleComponents']['4']];eyes=[bpy.data.objects[a['visibleComponents'][str(i)]] for i in (0,1)];ctrl=bpy.data.objects['AFN59_FACE_CONTROLS'];ctrl.animation_data.action=None
    for o in [body]+eyes:
        for md in o.modifiers:
            if md.type=='SUBSURF':md.levels=md.render_levels
    result={'source':a['output'],'sourceSha256':a['outputSha256'],'poses':{},'scope':'Actual closed body/oral/socket tissue surface and two closed optical outer shells; no iris-volume, full body self, fibre or continuous-motion pass.'}
    for label,left,right in [('neutral',0.,0.),('quarter',.25,.25),('half',.5,.5),('threeQuarter',.75,.75),('closed',1.,1.),('leftWink',1.,0.),('rightWink',0.,1.)]:
        ctrl['blink_left']=left;ctrl['blink_right']=right;ctrl.update_tag();bpy.context.view_layer.update();row=k.mesh(body);V,T=row['V'],row['T'];tree=k.selfcheck.tree(V,T);tri=V[T];out={'controls':[left,right],'anchors':{}}
        if label=='neutral':result['actualBodySurfaceTopology']=edges(T)
        for eye in eyes:
            eo=k.mesh(eye);P,U=eo['V'],eo['T'];centre=(P.min(0)+P.max(0))*.5;et=k.selfcheck.tree(P,U);bodyState=k.f.flowcheck.cap.solid.classify(tree,tri,Vector(centre));ownState=k.f.flowcheck.cap.solid.classify(et,P[U],Vector(centre));out['anchors'][eye.name]={'classificationAgainstBody':bodyState,'classificationAgainstOwnOpticalShell':ownState,'worldPointM':centre.tolist(),'anchorOnlyUnsignedBodyDistanceM':float(tree.find_nearest(Vector(centre))[3])}
            if label=='neutral':out['anchors'][eye.name]['actualOuterShellTopology']=edges(U)
        result['poses'][label]=out;k.save('b-cavity-volume-verification.json',result);print('R60_CAVITY_VOLUME',label,{name:r['classificationAgainstBody'] for name,r in out['anchors'].items()},flush=True)
    topology=result['actualBodySurfaceTopology'];good=topology['boundaryEdges']==topology['nonManifoldEdges']==0 and all(row['classificationAgainstBody']=='outside' and row['classificationAgainstOwnOpticalShell']=='inside' for pose in result['poses'].values() for row in pose['anchors'].values());result['status']='PASS_TESTED_CLOSED_TISSUE_AND_OCULAR_SPACE_SCOPE' if good else 'FAIL_OR_UNRESOLVED_CAVITY_VOLUME';result['seconds']=time.time()-tick;k.save('b-cavity-volume-verification.json',result);print('R60_CAVITY_VOLUME_SCOPE',result['status'],time.time()-tick,flush=True)
if __name__=='__main__':main()
