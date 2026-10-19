"""Own retained guides as artist stroke targets, not child path interpolation."""
import bpy,numpy as np
from mathutils.geometry import interpolate_bezier
from mathutils import Vector

def sample(o,count=128):
    points=[];sp=o.data.splines[0]
    for left,right in zip(sp.bezier_points,sp.bezier_points[1:]):
        points.extend(interpolate_bezier(left.co,left.handle_right,right.handle_left,right.co,33)[:-1])
    points.append(sp.bezier_points[-1].co.copy());P=np.array([o.matrix_world@p for p in points])
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))]
    return np.column_stack([np.interp(np.linspace(0,arc[-1],count),arc,P[:,j]) for j in range(3)])

def weights(roots,guideRoots):
    D=np.linalg.norm(roots[:,None]-guideRoots[None],axis=2)
    sides=(roots[:,None,0]*guideRoots[None,:,0]>=0)
    D[~sides]=1e5;near=np.argsort(D,axis=1)[:,:2]
    W=np.zeros_like(D)
    dd=np.take_along_axis(D,near,axis=1)
    ww=np.exp(-(dd-dd[:,0,None])/.008);ww/=ww.sum(1)[:,None]
    np.put_along_axis(W,near,ww,axis=1)
    return W

def plan(Pworld):
    objects=sorted([o for o in bpy.data.objects if o.name.startswith('AFN48_CTRL_')],key=lambda o:o.name)
    G=np.array([sample(o,Pworld.shape[1]) for o in objects]);W=weights(Pworld[:,0],G[:,0]);result=[]
    for gi,o in enumerate(objects):
        selected=W[:,gi]>.35
        if selected.sum()<30:continue
        for fraction,label in ((.18,'root_volume'),(.49,'middle_wave'),(.85,'tip_turn')):
            index=int(fraction*(Pworld.shape[1]-1));start=np.median(Pworld[selected,index],axis=0)
            target=G[gi,index];delta=target-start
            # A finite artist stroke, not a demand to attain an unreachable
            # guide length or a contact tolerance change.
            if np.linalg.norm(delta)>.045:delta*=.045/np.linalg.norm(delta)
            side=start[:2]-np.array((0,-.014));side/=max(np.linalg.norm(side),1e-9)
            angle=.90;view=(side[0]*np.cos(angle)-side[1]*np.sin(angle),side[0]*np.sin(angle)+side[1]*np.cos(angle),.10)
            result.append({'name':o.name+'_'+label,'view':view,'knots':[start.tolist(),(start+delta*.55).tolist(),(start+delta).tolist()],
                           'radius':145,'strength':.75,'guideIndex':gi,'guideObject':o.name,'referenceFraction':fraction,
                           'sourceSectionCurves':int(selected.sum()),'purpose':'Native length/collision-constrained whole-section sculpt; no per-root guide copying or generated followers.'})
    return result,G[:,0],[o.name for o in objects]
