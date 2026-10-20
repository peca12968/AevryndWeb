"""Complete short-crop authoring on the coherent r60 woman.

Own scalp tangent flow, region lengths and separated local tuft perturbations.
No shared tie target, donor hair, old Bob, normal-seed Comb or proxy shell.
This is a complete static hairstyle trial, not accepted hair mechanics.
"""
from pathlib import Path
import bpy, numpy as np, json, hashlib, importlib.util, time, math, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree

R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source'
E=R/'Evidence/character-female-next/r0063-layered-crop';E.mkdir(parents=True,exist_ok=True)
SRC=S/'aevrynd-female-next-r0060-b-limit-surface-assembly-study.blend'
OUT=S/'aevrynd-female-next-r0063-a-side-part-crop-study.blend'
NAME='AFN63_SCALP_ATTACHED_LAYERED_CROP';N=72

def module(n,p):
    sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
g=module('groom63base','build-female-next-r0061-surface-flow-groom.py')
shade=module('shade63base','shade-female-next-r0061-physical-hair.py')

def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def unit(v):return v/max(np.linalg.norm(v),1e-20)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def field(d):
    # Off-centre longitudinal part. The two sides sweep AWAY from the part;
    # occipital flow turns down the nape rather than converging to a tie.
    side=1. if d[0]+.20*d[2]>=0 else -1.
    rear=np.clip((d[1]-.05)/.7,0,1)
    target=np.array((side*(.85-.55*rear),.18+.20*rear,-.16-.85*rear))
    t=target-d*(target@d)
    if np.linalg.norm(t)<1e-5:t=np.cross(d,np.array((0.,1.,0.)))
    return unit(t)

def author(row):
    P,T=row['V'],row['T'];ids=np.flatnonzero(np.isin(row['mi'],(4,5))&(P[T,2].min(1)>1.355))
    tree=BVHTree.FromPolygons(P.tolist(),T[ids].tolist(),all_triangles=True)
    C=np.array((0.,-.038,1.471));axes=np.array((.073,.096,.090))
    def surface(d):
        ray=unit(d*axes);h=tree.ray_cast(Vector(C+ray*.4),Vector(-ray),.65)
        if h[0] is None:raise ValueError(('Scalp chart miss',d.tolist()))
        ti=int(ids[h[2]]);A=P[T[ti]];w=np.linalg.lstsq((A[1:]-A[0]).T,np.array(h[0])-A[0],rcond=None)[0];bc=np.r_[1-w.sum(),w]
        assert bc.min()>-1e-4
        return bc@A,unit(np.array(h[1])),ti,bc
    # Equal-area deterministic follicles. No random tie, no deletion in
    # response to contact failures, no radius/density parameter sweep.
    candidate_count=42000;idx=np.arange(candidate_count);z=1-2*(idx+.5)/candidate_count
    az=idx*(math.pi*(3-math.sqrt(5)));D=np.column_stack((np.sqrt(1-z*z)*np.sin(az),-np.sqrt(1-z*z)*np.cos(az),z))
    Q=[];records=[];regions=[];tufts=[];rejected=[];lens=[]
    for ii,d0 in enumerate(D):
        az0=math.atan2(d0[0],-d0[1]);theta=math.acos(d0[2]);front=(1+math.cos(az0))*.5
        limit=2.28-1.18*front**1.35+.018*math.sin(7*az0)
        if theta>=limit:continue
        root,n0,ti,bc=surface(d0)
        # Explicit pinna/ear-base exclusion from actual source landmarks;
        # this is the designed growth domain, never a failed-root filter.
        if abs(root[0])>.063 and -.055<root[1]<.020 and root[2]<1.481:
            rejected.append({'index':int(ii),'sourceFace':int(row['nativeTriangleFace'][ti]),'reason':'pinna outside scalp domain'});continue
        # 7--11 mm authored local tuft domains; only a subtle directional
        # perturbation, never one common clump endpoint or zero-radius tip.
        tx=int(math.floor((root[0]+.10)/.009));ty=int(math.floor((root[1]+.15)/.010));tz=int(math.floor((root[2]-1.35)/.011))
        tuft=(tx*73856093 ^ ty*19349663 ^ tz*83492791)&0x7fffffff
        phase=(tuft%997)/997*math.tau;fiber_phase=(ii*.754877666)%1*math.tau
        top=np.clip((d0[2]-.15)/.85,0,1);rear=np.clip((d0[1]-.1)/.8,0,1)
        length=(.026+.044*top+.014*front*top)*(1+.12*math.sin(phase)+.06*math.sin(fiber_phase))
        region=0 if top>.55 else (1 if rear>.35 else 2)
        s=np.r_[0.,.00025,np.linspace(.001,length,N-2)];d=d0.copy();path=[];prev=0.
        for j,at in enumerate(s):
            if j:
                # Integrate the comb direction in the anatomical chart.
                t=field(d);cross=unit(np.cross(d,t));t=unit(t+.075*math.sin(phase)*cross)
                d=unit(d+(at-prev)/.085*t)
            foot,n,_,_=surface(d);u=at/length
            lift=.0038*(1-math.exp(-at/.004))+(.004+.010*top)*math.sin(math.pi*u)**.85
            # Spatial variation is coherent inside a tuft and fades at root.
            lift+=(.0015*math.sin(phase)+.00035*math.sin(fiber_phase+u*5))*math.sin(math.pi*u)
            path.append(foot+n*lift);prev=at
        path=np.array(path);path[0]=root
        Q.append(path);records.append((ti,int(row['nativeTriangleFace'][ti]),*bc));regions.append(region);tufts.append(tuft);lens.append(length)
        if len(Q)%1500==0:print('R63_ACTUAL_CROP_FIBRES',len(Q),flush=True)
    Q=np.array(Q,'f4');rr=np.full(Q.shape[:2],.000035,'f4');rr*=np.maximum(.06,np.minimum(1,(1-np.linspace(0,1,N))/.19))[None,:]
    return Q,rr,np.array(records),np.array(regions,'i4'),np.array(tufts,'i4'),{'actualFibres':len(Q),'tuftDomains':len(set(tufts)),'growthDomainExclusions':rejected,'lengthRangeM':[min(lens),max(lens)]}

def material():
    mat=bpy.data.materials.new('AFN63_CHIANG_SAME_FIXED_R61_PARAMETERS');mat.use_nodes=True;t=mat.node_tree;t.nodes.clear();out=t.nodes.new('ShaderNodeOutputMaterial');hair=t.nodes.new('ShaderNodeBsdfHairPrincipled');hair.model='CHIANG';hair.parametrization='MELANIN'
    for n,v in {'Melanin':.65,'Melanin Redness':.20,'Roughness':.38,'Radial Roughness':.36,'IOR':1.55,'Random Color':.12,'Random Roughness':.08}.items():hair.inputs[n].default_value=v
    info=t.nodes.new('ShaderNodeHairInfo');t.links.new(info.outputs['Random'],hair.inputs['Random']);t.links.new(hair.outputs[0],out.inputs['Surface']);return mat

def main():
    tick=time.time();g.E=E;g.k.f.E=E;shade.g.E=E
    if '--views' in sys.argv:
        summary=json.loads((E/'a-build-summary.json').read_text());assert sha(OUT)==summary['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(OUT));shade.settings()
        views=('oblique','opposite-oblique','alternate-oblique','body-face');save('a-additional-view-controls.json',shade.render('a-crop',views));return
    assert not OUT.exists();assert sha(SRC)==g.SOURCE_SHA
    save('round-contract.json',{'previousGoalTurnClassification':'progress: v17 prompt and entry points saved, GitHub2e35b6c verified; no model quality change.',
        'sixLines':[
            'Exact r60B complete woman SHA3324231...; no live heavy job. r62 remains unregistered static-bundle research and failed discrete continuous-contact trial.',
            'Main: near-bald scalp and rejected cap/funnel hairstyles. Secondary: flat skin/eye response. Select complete haircut structure.',
            'Deliver a complete editable short side-part crop on the same woman, visible scalp transitions and layered ends, complete head/body comparisons.',
            'Native scalp follicle/guide/clump principles; own region-specific tangent flow, off-centre part, local tuft variation. No gathered tie or old Bob geometry.',
            'One actual finite-fibre candidate. First complete face/profile/back preview; reject helmet, mushroom, bristles, missing coverage or no whole-head benefit. No density/radius sweep.',
            'One heavy job/4threads; first diagnosis10min, preview before45min; motion is not authored this round and remains required later.'
        ],'references':[{'url':'https://docs.blender.org/manual/en/3.5/modeling/geometry_nodes/hair/guides/clump_hair_curves.html','use':'Guide mapping/local clumps and tip spread principle; own authoring, no node asset or third-party hairstyle copied.'}],
        'r62Reconciliation':{'source':'aevrynd-female-next-r0062-a-packed-bundle-study.blend','sha256':'76da364d04c00dfbdc36592d279ead78f196fc123cefff3b17dbe3b9c634fc00','adopted':False,'staticScope':'61 shafts only, body/self static passed','motion':'Discrete published first interval failed unchanged1um continuous numerical-clearance gate; no actual negative penetration established for every flagged witness. No full motion qualification.','nextAction':'Preserve evidence. Do not resume rejected discrete run or treat isolated shaft prototype as a full hairstyle.'}})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1);stage=g.k.f.v.stage();body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];levels=[]
    for md in body.modifiers:
        if md.type=='SUBSURF':levels.append((md,md.levels));md.levels=md.render_levels
    bpy.context.view_layer.update();row=g.k.mesh(body);Q,rr,rec,region,tufts,info=author(row)
    old=bpy.data.objects['AFN57_CANONICAL_BOB_GUIDES'];old.hide_render=True;old.hide_set(True)
    ob=g.create_curves(NAME,Q,rr);ob.data.materials.clear();ob.data.materials.append(material())
    for name,kind,values,field in [('AFN63_RestRenderTriangle','INT',rec[:,0].astype('i4'),'value'),('AFN63_NativeScalpFace','INT',rec[:,1].astype('i4'),'value'),('AFN63_RestBarycentric','FLOAT_VECTOR',rec[:,2:].astype('f4'),'vector'),('AFN63_Region','INT',region,'value'),('AFN63_TuftDomain','INT',tufts,'value')]:ob.data.attributes.new(name,kind,'CURVE').data.foreach_set(field,values.ravel())
    ob['scope']='Complete static short-crop hairstyle trial. Actual35um fibres and source-rest lineage. No accepted body/self/root-join/dynamics/runtime claim.'
    for md,level in levels:md.levels=level
    assert g.k.f.v.stage()==stage
    np.savez_compressed(E/'a-crop-authoring.npz',positions=Q,radii=rr,rootRecords=rec,regions=region,tufts=tufts)
    settings=shade.settings();g.k.b.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.context.scene['AFN63_status']='UNACCEPTED_COMPLETE_CROP_STYLE_TRIAL'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'info':info,'pointsPerCurve':N,'radiusM':float(rr.max()),'settings':settings,'skinBodyOpticsLightsUnchanged':True,'dynamicsAuthored':False,'contactStatus':'UNTESTED','secondsBeforePreview':time.time()-tick})
    save('a-first-view-controls.json',shade.render('a-crop',('face','profile','back')));print('R63_COMPLETE_PREVIEW_READY',time.time()-tick,flush=True)

if __name__=='__main__':main()
