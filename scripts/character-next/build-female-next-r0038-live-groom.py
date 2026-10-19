"""Own live native-curve guide DELTA authoring, not a new hairstyle or simulation.
Retains all existing rest fibres. Editable guides change followers through a
same-part three-neighbor delta basis. Rest zero must be bit-exact on reopening.
"""
import bpy,importlib.util,json,time,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
sp=importlib.util.spec_from_file_location('f38',Path(__file__).with_name('build-female-next-r0038-volume-flow.py'));f=importlib.util.module_from_spec(sp);sp.loader.exec_module(f)
b=f.b;v=f.v;S=f.S;E=f.E;SRC=f.SRC
OUT=S/'aevrynd-female-next-r0038-b-live-groom-authoring.blend'
GUIDE='AFN38_B_EDIT_SCALP_GUIDES';REST='AFN38_B_GUIDE_REST';N=128
def eval_arrays(o):
    bpy.context.view_layer.update()
    eo=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return v.hair_arrays(eo)
def select_guides(roots,parts):
    ids=[]
    for part in (-1,1):
        domain=np.flatnonzero(parts==part);P=roots[domain]
        chosen=[int(np.argmax(P[:,2]))];d=np.full(len(P),np.inf)
        for k in range(128):
            delta=P-P[chosen[-1]];d=np.minimum(d,np.einsum('ij,ij->i',delta,delta))
            if k<127:chosen.append(int(np.argmax(d)))
        ids.extend(domain[chosen].tolist())
    return np.array(sorted(ids),dtype='i4')
def bindings(roots,parts,ids):
    index=np.empty((len(roots),3),dtype='i4');weights=np.empty((len(roots),3),dtype='f4')
    for part in (-1,1):
        src=np.flatnonzero(parts==part);gi=np.flatnonzero(parts[ids]==part)
        D=np.sum((roots[src,None]-roots[ids[gi]][None,:])**2,axis=2)
        order=np.argsort(D,axis=1)[:,:3];ds=np.take_along_axis(D,order,axis=1)
        w=1/np.maximum(ds,1e-16);w/=w.sum(1)[:,None]
        index[src]=gi[order];weights[src]=w
    return index,weights
def subset(hair,ids,name):
    d=hair.data.copy();d.name=name
    keep=set(map(int,ids));d.remove_curves(indices=[k for k in range(len(d.curves)) if k not in keep])
    o=hair.copy();o.data=d;o.name=name
    for k in list(o.keys()):del o[k]
    bpy.context.scene.collection.objects.link(o);o.hide_render=True;o.hide_set(False)
    o['aevrynd_layer']='EDITABLE_SCALP_GUIDES' if name==GUIDE else 'AUTHORING_GUIDE_REST_REFERENCE'
    return o
def graph(hair,guide,rest):
    ng=bpy.data.node_groups.new('AFN38_B_NATIVE_GUIDE_DELTAS','GeometryNodeTree');ng.is_modifier=True
    ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes=ng.nodes;links=ng.links
    def node(t,name=None):
        n=nodes.new(t)
        if name:n.label=name;n.name=name
        return n
    def math(op,A,B=None):
        n=node('ShaderNodeMath');n.operation=op
        for inp,val in zip(n.inputs,(A,B)):
            if val is None:continue
            if isinstance(val,(int,float)):inp.default_value=val
            else:links.new(val,inp)
        return n.outputs[0]
    def vector(op,A,B):
        n=node('ShaderNodeVectorMath');n.operation=op;links.new(A,n.inputs[0]);links.new(B,n.inputs[1]);return n.outputs[0]
    info=[]
    for target in (guide,rest):
        n=node('GeometryNodeObjectInfo',target.name);n.transform_space='RELATIVE';n.inputs['Object'].default_value=target;n.inputs['As Instance'].default_value=False;info.append(n.outputs['Geometry'])
    pos=node('GeometryNodeInputPosition').outputs['Position'];idx=node('GeometryNodeInputIndex').outputs['Index']
    cv=math('FLOORED_MODULO',idx,N)
    sums=None
    for k in range(3):
        gi=node('GeometryNodeInputNamedAttribute');gi.data_type='INT';gi.inputs['Name'].default_value='AFN38_Guide'+str(k)
        weight=node('GeometryNodeInputNamedAttribute');weight.data_type='FLOAT';weight.inputs['Name'].default_value='AFN38_Weight'+str(k)
        lookup=math('ADD',math('MULTIPLY',gi.outputs['Attribute'],N),cv)
        sampled=[]
        for geom in info:
            sn=node('GeometryNodeSampleIndex');sn.data_type='FLOAT_VECTOR';sn.domain='POINT';sn.clamp=False
            links.new(geom,sn.inputs['Geometry']);links.new(pos,sn.inputs['Value']);links.new(lookup,sn.inputs['Index']);sampled.append(sn.outputs['Value'])
        delta=vector('SUBTRACT',*sampled)
        mask=math('GREATER_THAN',cv,0)
        amount=math('MULTIPLY',weight.outputs['Attribute'],mask)
        scale=node('ShaderNodeVectorMath');scale.operation='SCALE';links.new(delta,scale.inputs[0]);links.new(amount,scale.inputs['Scale'])
        sums=scale.outputs[0] if sums is None else vector('ADD',sums,scale.outputs[0])
    inp=node('NodeGroupInput');out=node('NodeGroupOutput');setpos=node('GeometryNodeSetPosition')
    links.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);links.new(sums,setpos.inputs['Offset']);links.new(setpos.outputs['Geometry'],out.inputs['Geometry'])
    for j,n in enumerate(nodes):n.location=((j%7)*210,-(j//7)*180)
    m=hair.modifiers.new('AFN38_LiveEditableGuideDelta','NODES');m.node_group=ng
    return ng
def main():
    start=time.time();assert b.sha(SRC)=='4d14d272a7ad71b4b5f0fff1d60e793001e7e1620e69636feac8c6c5837db0b9'
    f.save('b-round-contract.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),
      'type':'FUNCTIONAL_AUTHORING_REPAIR_NO_APPEARANCE_INCREASE',
      'blocker':'Every full style has required offline field regeneration; independent guide edits do not yet control the complete current hair live in Blender.',
      'reasonForSecondCandidate':'A autonomous whole-head flow visibly rejected: symmetric lateral bulges and coherent sheets. B repairs the manual authoring basis instead of tuning A.',
      'method':'Own Blender native node graph samples edited minus rest guide positions; same-part3-neighbor weights distribute deltas to existing rest fibres, CV0 explicitly fixed.',
      'expectedDifference':'Rest complete head bit-exact; in-edit local guide changes visibly deform bounded followers without a new generator or root movement.',
      'minimumTest':'Rest eval exact; deliberate guide deformation has affected followers, all roots fixed, opposite part untouched; restore exact; save/reopen and compare.',
      'reject':['Any rest geometry/radius/material/stage drift','Any actual root movement during guide editing','No live influence or wrong-part influence'],
      'candidateCountThisRound':2,'scope':'Offline editable authoring only. Not a natural hairstyle, surface-deforming scalp rig, simulation, collision-safe edit, engine integration or score increase.',
      'references':['https://docs.blender.org/manual/en/5.1/modeling/geometry_nodes/geometry/sample/sample_index.html','https://docs.blender.org/manual/en/5.1/modeling/geometry_nodes/geometry/write/set_position.html'],
      'referenceBoundary':'Manual fetch failed; installed5.2.2RNA and evaluator are authoritative API verification. Own graph/data; no external groom/node code.'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;b.setup(s,b.config(s))
    before=f.state();hair=bpy.data.objects[f.OLD];p,r=v.hair_arrays(hair)
    data=np.load(S/'aevrynd-female-next-r0033-c-bob-fibres.npz');parts=data['parts']
    ids=select_guides(p[:,0].astype('f8'),parts);indices,weights=bindings(p[:,0].astype('f8'),parts,ids)
    guide=subset(hair,ids,GUIDE);rest=subset(hair,ids,REST);rest.hide_set(True)
    guide['instructions']='Select this object, enter Sculpt Mode or Edit Mode, edit CVs after the follicle. Followers update live. Rest body is static; edited contacts need revalidation.'
    guide['scope']='Authoring controls only; guide radius is not a displayed physical strand.'
    gp,gr=v.hair_arrays(guide);assert np.array_equal(gp,p[ids])
    guide.data.attributes['radius'].data.foreach_set('value',np.full(gr.size,.00016,dtype='f4'))
    for k in range(3):
        a=hair.data.attributes.new('AFN38_Guide'+str(k),'INT','CURVE');a.data.foreach_set('value',indices[:,k])
        a=hair.data.attributes.new('AFN38_Weight'+str(k),'FLOAT','CURVE');a.data.foreach_set('value',weights[:,k])
    ng=graph(hair,guide,rest);ep,er=eval_arrays(hair)
    assert np.array_equal(ep,p) and np.array_equal(er,r),('rest drift',float(np.max(np.abs(ep-p))))
    assert f.state()==before
    # Verify live authoring with a local group on the right front. No animation
    # qualification is inferred; this deliberately edited pose is not adopted.
    roots=p[ids,0];domain=np.flatnonzero((parts[ids]>0)&(roots[:,1]<-.03))
    control=int(domain[np.argmin(np.sum((roots[domain]-np.array((.055,-.08,1.52)))**2,axis=1))])
    test=gp.copy();t=np.linspace(0,1,N);test[control,:,0]+=(.006*np.sin(.5*np.pi*t)**2).astype('f4');test[control,0]=gp[control,0]
    guide.data.position_data.foreach_set('vector',test.ravel());guide.data.update_tag()
    qp,qr=eval_arrays(hair);changed=np.any(qp!=p,axis=(1,2));expected=np.any(indices==control,axis=1)
    assert changed.any() and np.all(~changed|expected) and np.all(parts[changed]>0)
    assert np.array_equal(qp[:,0],p[:,0]) and np.array_equal(qr,r)
    moved=float(np.max(np.linalg.norm(qp.astype('f8')-p,axis=2)))
    f.render('b-control-demo',('oblique',))
    guide.data.position_data.foreach_set('vector',gp.ravel());guide.data.update_tag()
    ep,er=eval_arrays(hair);assert np.array_equal(ep,p) and np.array_equal(er,r)
    assert f.state()==before
    np.savez_compressed(S/'aevrynd-female-next-r0038-b-live-guide-bindings.npz',
        guideRootIds=ids,indices=indices,weights=weights,guideRestPositions=gp)
    hair['AFN38_live_authoring']='Own native same-part delta guide graph. Neutral rest equalsr37C; altered grooms require separate visual/contact checks.'
    s['AFN38_status']='RETAIN_LIVE_AUTHORING_REST_EXACT_NO_APPEARANCE_CHANGE'
    b.camera('face');s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    f.save('b-build.json',{'output':str(OUT),'outputSha256':b.sha(OUT),'sourceState':before,
        'restEvaluatedPositionsRadiiExact':True,'rootsFixedInDeliberateEdit':True,
        'guideCount':len(ids),'fibres':len(p),'pointsPerFibre':N,'neighborsPerFibre':3,
        'controlTest':{'guideIndex':control,'sourceRootId':int(ids[control]),'affectedFibres':int(changed.sum()),'allowedFollowerFibres':int(expected.sum()),'maximumMovedPointM':moved,'oppositePartChanged':False,'editContacts':'NOT_TESTED_NOT_ADOPTED'},
        'nodes':len(ng.nodes),'scope':'Live offline authoring only; static scalp binding not deforming body rig; no natural hair/self/dynamics/runtime acceptance.',
        'decision':'AWAIT_REOPEN_PROOF','seconds':time.time()-start})
    print('R38_LIVE_AUTHORING_BUILT',len(ids),int(changed.sum()),time.time()-start,flush=True)
if __name__=='__main__':main()
