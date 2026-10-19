"""Bounded alternative: authored quad-rail guides with explicit new roots.

This is not transfer of the stopped private groom or old curtain deformation.
No displacement is applied to hide contacts. Failed guides forbid expansion.
"""
import bpy,importlib.util,json,time,numpy as np
from pathlib import Path
from mathutils import Vector
sp=importlib.util.spec_from_file_location('rails47',Path(__file__).with_name('inspect-female-next-r0047-card-layout.py'));c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
a=c.a;b=a.b;f=a.f;E=a.E;S=a.S;OUT=S/'aevrynd-female-next-r0047-b-authored-rail-pilot.blend'
contact=f.flowcheck.module('caps47','build-female-next-r0033-parted-bob.py')
def main():
    start=time.time();bpy.ops.wm.open_mainfile(filepath=str(a.OUT));before=f.state();cards=bpy.data.objects['AFN47_CC0_Bob02_AuthoredCards'];rows=c.columns(cards.data);M=np.array([v.co[:]for v in cards.data.vertices]);V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=a.i.i.tree(V,T);P=[];bindings=[]
    for index,row in enumerate(rows):
        rail=np.array(row['rails']);knots=M[rail].mean(1);d=np.linalg.norm(np.diff(knots,axis=0),axis=1);t=np.r_[0,np.cumsum(d)];t/=t[-1];u=np.linspace(0,1,128);path=np.column_stack([np.interp(u,t,knots[:,j])for j in range(3)])
        # Declare new follicles on actual anatomical crown before testing. Only
        # a proximal connection changes; free artist guide is not body-pushed.
        hit,n,tid,dist=tree.find_nearest(Vector(path[0]));n=np.array(n);root=np.array(hit)+n*.00015;delta=root-path[0];fade=np.maximum(0,1-u/.15);fade=fade*fade*(3-2*fade);path+=delta[None,:]*fade[:,None];path[0]=root
        tri=V[T[tid]];xy=np.linalg.lstsq(np.column_stack((tri[1]-tri[0],tri[2]-tri[0])),np.array(hit)-tri[0],rcond=None)[0];bc=np.r_[1-xy.sum(),xy];assert bc.min()>-1e-3
        P.append(path);bindings.append({'guide':index,'bodyTriangle':int(tid),'barycentric':bc.tolist(),'rootOffsetM':.00015,'normal':n.tolist(),'rootM':root.tolist(),'originalGuideStartM':knots[0].tolist(),'connectionLengthFraction':.15,'sourceRails':row['rails'],'scope':'New static anatomical crown follicle from authored column peak. Not a moving-scalp rig, not an inherited root certificate, not moved in response to a contact failure.'})
    P=np.array(P);r=np.broadcast_to(np.linspace(.00004,.000003,128),(len(P),128)).copy();audit=contact.check(P,r,tree,V[T]);a.save('b-guide-body-contact.json',audit);a.save('b-guide-root-bindings.json',{'roots':bindings});np.savez_compressed(E/'b-pilot-paths.npz',positions=P.astype('f4'),radii=r.astype('f4'))
    cards.hide_render=True;cards.hide_set(True);o=contact.guides(P,bpy.data.objects[b.BODY],bpy.data.objects['AFN33_C_BODY_BOUND_FIBRES'].data.materials[0]);o.name='AFN47_B_AUTHORED_RAIL_GUIDES';o.data.bevel_depth=.00004
    for spline in o.data.splines:spline.points.foreach_set('radius',np.linspace(1,.075,128).astype('f4'))
    # Do not densify a shape whose representative finite capsules fail.
    bpy.context.scene['AFN47_B_status']='PILOT_ONLY_NO_EXPANSION_UNLESS_CONTACT_AND_FORM_PASS';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);a.save('b-pilot-summary.json',{'output':str(OUT),'outputSha256':b.sha(OUT),'guides':len(P),'pointsPerGuide':128,'method':'Own exact opposite-quad-edge transport, split at crown peak, piecewise-linear paired-rail center; explicit new scalp root and proximal15percent connection only','distinctFromCandidateA':'Actual thin closed guide tubes replace broad textured cards. Not a material/density variation or an accepted full hairstyle.','candidatePolicy':'No dense fibres if representative actual finite capsules fail. No contact-driven root moves or free-length point projection.','bodyContact':audit['status'],'expansionAllowed':audit['status']=='PASS_TESTED_STATIC_CAPSULES','seconds':time.time()-start,'scope':'Feasibility on complete same character, guide-only static contact; optics/self/dynamic/runtime unqualified.'});f.E=E;f.render('b-pilot',('face','oblique','profile'));a.i.ch.review.extras('b-pilot',E);print('R47_B_PILOT',len(P),audit['status'],flush=True)
if __name__=='__main__':main()
