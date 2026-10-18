"""Separate native-data blink keys, with skin-frame lash and brow transport."""
import bpy,json,importlib.util,hashlib,time,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('build-female-next-r0018-layered-brows.py'));prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
R,S,solid=prior.R,prior.S,prior.solid;E=R/'Evidence/character-female-next/r0019-blink';SRC=S/'aevrynd-female-next-r0018-c-triangulated-brows-study.blend';VARIANT='c' if '--angular' in sys.argv else 'b' if '--seam' in sys.argv else 'a';DST=S/('aevrynd-female-next-r0019-c-angular-blink-study.blend' if VARIANT=='c' else 'aevrynd-female-next-r0019-b-seam-blink-study.blend' if VARIANT=='b' else 'aevrynd-female-next-r0019-a-native-blink-study.blend')
sha=prior.sha
def save(name,data):(E/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def positions(o):return np.array([tuple(v.co) for v in o.data.vertices],np.float32)
def frame(tri):
    x=tri[1]-tri[0];x/=np.linalg.norm(x);z=np.cross(tri[1]-tri[0],tri[2]-tri[0]);z/=np.linalg.norm(z);y=np.cross(z,x);return np.column_stack((x,y,z))
def add_key(o,name,p):
    if not o.data.shape_keys:o.shape_key_add(name='Basis',from_mix=False)
    key=o.shape_key_add(name=name,from_mix=False);key.relative_key=o.data.shape_keys.key_blocks[0];key.data.foreach_set('co',np.asarray(p,dtype=np.float32).ravel());key.value=0.;return key
def set_blink(left,right):
    rig=bpy.data.objects['AFN_R0005_Rig']
    if 'AFN19_Blink_L' in rig:
        rig['AFN19_Blink_L']=left;rig['AFN19_Blink_R']=right;rig.update_tag();bpy.context.view_layer.update();return
    for o in bpy.data.objects:
        if o.type=='MESH' and o.data.shape_keys:
            for side,value in (('L',left),('R',right)):
                key=o.data.shape_keys.key_blocks.get('AFN19_Blink_'+side)
                if key:key.value=value
    bpy.context.view_layer.update()

def build():
    assert VARIANT=='a','Use build-female-next-r0019-seam-blink.py for B'
    started=time.time();transfer=json.loads((E/'native-delta-transfer.json').read_text());assert transfer['status']=='PASS_EXACT_NATIVE_SUBDIVISION_CORRESPONDENCE' and transfer['sourceSha256']==sha(SRC) and transfer['cacheSha256']==sha(transfer['cache'])
    bpy.ops.wm.open_mainfile(filepath=str(SRC));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');before=prior.controls();body=bpy.data.objects['AFN_R0008_Body'];P=positions(body);data=np.load(transfer['cache']);assert np.array_equal(data['neutralBody'],P)
    fields={side:data['delta'+side].astype(np.float64) for side in ('L','R')};bodyMatrix=np.array(body.matrix_world,dtype=np.float64);W=P.astype(np.float64)@bodyMatrix[:3,:3].T+bodyMatrix[:3,3];worldFields={s:d@bodyMatrix[:3,:3].T for s,d in fields.items()}
    for side,d in fields.items():add_key(body,'AFN19_Blink_'+side,P.astype(np.float64)+d)
    lashPath=R/'Evidence/character-female-next/r0010-eye-rim/c-spaced-lashes-lash-bindings.json';browPath=S/'aevrynd-female-next-r0018-c-brow-bindings.json';bindings=json.loads(lashPath.read_text())+json.loads(browPath.read_text());groups={name:[r for r in bindings if r['object']==name] for name in sorted({r['object'] for r in bindings})};transport=[]
    for name,records in groups.items():
        o=bpy.data.objects[name];base=positions(o);M=np.array(o.matrix_world,dtype=np.float64);inverse=np.linalg.inv(M);world=base.astype(np.float64)@M[:3,:3].T+M[:3,3];radial=6 if name.startswith('AFN10_') else 5
        for side in ('L','R'):
            target=world.copy();moves=[]
            for rec in records:
                ids=np.array(rec['bodyVertices'],np.int64);delta=worldFields[side][ids]
                if not np.any(delta):continue
                tri0=W[ids];tri1=tri0+delta;F0,F1=frame(tri0),frame(tri1);rot=F1@F0.T;bc=np.array(rec['barycentric']);a0=bc@tri0;a1=bc@tri1;start=rec['firstVertex'];end=start+rec['vertices'];target[start:end]=(world[start:end]-a0)@rot.T+a1;moves.append(float(np.linalg.norm(target[start:end]-world[start:end],axis=1).max()))
            targetLocal=target@inverse[:3,:3].T+inverse[:3,3]
            if moves:add_key(o,'AFN19_Blink_'+side,targetLocal)
            transport.append({'object':name,'side':side,'fibres':len(records),'movedFibres':len(moves),'maximumVertexMoveM':max(moves) if moves else 0.,'method':'Rigid per-fibre transport in the actual bound skin-triangle frame; basis shape/length preserved at full key, no head-only frozen lashes.'})
    hairBindings=json.loads((S/'aevrynd-female-next-r0014-root-bindings.json').read_text());hairRoot=[]
    for side,d in fields.items():
        ds=np.array([np.array(r['barycentric'])@d[np.array(r['bodyVertices'])] for r in hairBindings]);hairRoot.append({'side':side,'maximumInheritedScalpRootDisplacementM':float(np.linalg.norm(ds,axis=1).max()),'rootBindings':len(hairBindings)})
    assert all(x['maximumInheritedScalpRootDisplacementM']==0 for x in hairRoot),hairRoot
    set_blink(0.,0.);assert prior.controls()==before
    bpy.context.scene['aevrynd_revision']='female-next-r0019-a';bpy.context.scene['aevrynd_release_state']='NATIVE_BLINK_RESEARCH_PENDING_CONTACT_AND_VISUAL_GATES';bpy.context.scene['aevrynd_blink_controls']='AFN19_Blink_L/R body and transported lashes/brows; linear raw authored keys, not calibrated motion.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));set_blink(0.,0.);assert prior.controls()==before
    images=[{'name':i.name,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE'];assert all(x['packed'] for x in images) and not bpy.data.libraries
    save('a-build-verification.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(DST),'outputSha256':sha(DST),'neutralHeadSkinEyesLashesHairBrowsRigLightMaterialStateExact':True,'bodyKeys':['AFN19_Blink_L','AFN19_Blink_R'],'transport':transport,'scalpRoots':hairRoot,'bindingSources':[{'path':str(p),'sha256':sha(p)} for p in (lashPath,browPath)],'fileBytes':DST.stat().st_size,'packedImages':images,'wallSeconds':time.time()-started,'status':'REOPEN_NEUTRAL_AND_BINDING_CONTROL_PASS_COLLISION_PENDING','limits':['Linear full keys only; no in-between correction, natural timing or continuous contact proof.','Native closure data is a starting shape, not evidence of compatibility with the repaired current eye socket/optics.']})
    print('R0019_A_BUILD_REOPEN_PASS',flush=True)

def diagnose():
    build=json.loads((E/(VARIANT+'-build-verification.json')).read_text());assert sha(DST)==build['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(DST));solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=4;body=bpy.data.objects['AFN_R0008_Body'];eyes=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN6_')];optics={o.name:solid.data(o) for o in eyes};fits=solid.stage.eyes.helper_centres();rows=[];head=1.5624730926266572*.91
    for value in (0.,.5,1.):
        set_blink(value,value);V,T,tree=solid.data(body);pairs={name:len(tree.overlap(d[2])) for name,d in optics.items()};images=[]
        for view,location,target,res in (('face',(0.,-.90,head+.015),(0.,-.02,head),(1100,1100)),('eyes',(0.,-.43,fits['L']['centre'][2]+.005),(0.,-.115,fits['L']['centre'][2]),(1400,650))):
            c=s.camera;c.location=location;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100;s.render.resolution_x,s.render.resolution_y=res;s.render.resolution_percentage=100;path=E/f'{VARIANT}-blink-{value:.2f}-{view}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True);images.append(str(path))
        rows.append({'weight':value,'bodyOpticalTriangleIntersectionPairs':pairs,'renders':images});save(VARIANT+'-pilot-diagnosis.json',{'asset':str(DST),'assetSha256':sha(DST),'samples':rows,'scope':'Early pilot: three static blend weights, body-vs-optical surface pairs only. No complete collision, root intermediate constraint, full closure or motion acceptance.'});print('R0019_'+VARIANT.upper()+'_PILOT '+str(value)+' '+str(sum(pairs.values())),flush=True)
    set_blink(0.,0.)
if __name__=='__main__':
    if '--diagnose' in sys.argv:diagnose()
    else:build()
