"""A bounded native compression candidate fitted from measured open lip margins."""
import bpy,json,math,time,importlib.util
import numpy as np
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('base',Path(__file__).with_name('build-female-next-r0019-native-blink.py'));base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
R,S,SRC,solid=base.R,base.S,base.SRC,base.solid;E=R/'Evidence/character-female-next/r0023-neutral-mouth';DST=S/'aevrynd-female-next-r0023-a-neutral-mouth-study.blend';sha=base.sha
def save(name,obj):(E/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def controls():
    state=base.prior.controls();state['meshes'].pop('AFN_R0008_Body',None)
    # The existing audit intentionally excludes brows; include their geometry.
    state['browMeshes']={o.name:solid.geom(o) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN11_')};return state
def bary(point,tri):
    v=np.linalg.lstsq(np.column_stack((tri[1]-tri[0],tri[2]-tri[0])),point-tri[0],rcond=None)[0];return np.array((1-v.sum(),v[0],v[1]))
def aperture(tree,V,T,delta=None):
    rows=[]
    def ray(x,z):return tree.ray_cast(Vector((x,-.4,z)),Vector((0,1,0)),.5)
    for x in np.linspace(-.026,.026,27):
        openZ=[]
        for z in np.linspace(1.394,1.404,201):
            hit,n,face,d=ray(float(x),float(z))
            if hit is not None and hit.y>-.10:openZ.append(float(z))
        if not openZ:rows.append({'x':float(x),'sampledOpenHeightM':0.});continue
        row={'x':float(x)}
        for label,gap,skin in (('lower',min(openZ),min(openZ)-.00015),('upper',max(openZ),max(openZ)+.00015)):
            hit,n,face,d=ray(float(x),skin)
            while hit is not None and hit.y>-.10 and abs(skin-gap)<.002:
                skin+=.00015 if label=='upper' else -.00015;hit,n,face,d=ray(float(x),skin)
            assert hit is not None and hit.y<-.10
            for _ in range(14):
                z=(skin+gap)/2;hit,n,face,d=ray(float(x),z)
                if hit is not None and hit.y<-.10:skin=z
                else:gap=z
            z=skin+(.00003 if label=='upper' else -.00003);hit,n,face,d=ray(float(x),z);assert hit is not None;point=np.array(hit,np.float64);ids=np.array(T[face]);bc=bary(point,V[ids]);row[label+'Point']=point.tolist();row[label+'Vertices']=ids.tolist();row[label+'Barycentric']=bc.tolist()
            if delta is not None:row[label+'Delta']=(bc@delta[ids]).tolist()
        row['sampledOpenHeightM']=row['upperPoint'][2]-row['lowerPoint'][2];rows.append(row)
    return rows
def main():
    started=time.time();inspection=json.loads((E/'mouth-source-inspection.json').read_text());assert sha(SRC)==inspection['sourceSha256'] and sha(inspection['cache'])==inspection['cacheSha256'];bpy.ops.wm.open_mainfile(filepath=str(SRC));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');before=controls();body=bpy.data.objects['AFN_R0008_Body'];P=base.positions(body);data=np.load(inspection['cache']);assert np.array_equal(P,data['neutralBody']);delta=data['delta_compression'].astype(np.float64);V,T,tree=solid.data(body);V=np.array(V,np.float64);beforeRims=aperture(tree,V,T,delta);limits=[]
    desired=.00020
    for row in beforeRims:
        if row['sampledOpenHeightM']<=desired*1.5 or 'upperDelta' not in row:continue
        shrink=row['lowerDelta'][2]-row['upperDelta'][2]
        if shrink>1.e-7:limits.append((row['sampledOpenHeightM']-desired)/shrink)
    assert limits and min(limits)>0.;weight=min(1.,float(min(limits)));assert .01<weight<=1.,weight
    save('iteration-contract.json',{'previousGoalTurnClassification':'progress: own scalp/guide architecture implemented, complete-segment gates failed, expansion stopped, actual authoring review archived. No accepted realism gain.','stage':'B_COMPLETE_HEAD_IN_PROGRESS','source':str(SRC),'sourceSha256':sha(SRC),'primaryDefect':'Neutral lips protrude as rounded pillows around a visible empty mouth aperture.','hypothesis':'A positive native lip-compression field, limited by measured lip-margin movement, reduces the empty slit and excessive forward lip volume without a procedural annulus, covering strip or material change.','fitting':'At 27 frontal sections, estimate upper/lower skin-margin motion from actual bound triangles. Limit to the earliest predicted 0.20mm margin gap; then independently test actual surfaces. This is an estimate, not a global nonpenetration proof.','candidateWeight':weight,'rejectIf':['Changed lip/body nonadjacent self-intersections or overlap with existing oral/eye/attachment parts.','Unnatural pinched/inverted lip or no whole-face benefit under matching images.','Skin/material/light/eye/hair or unrelated source geometry changes.'],'budget':{'threads':4,'candidatesMaximum':3,'candidateCount':1,'bodyVertices':214050,'initialStaticStates':5},'licensing':'Native core graphical target data CC0; locally authored importer/transfer code, no MPFB program in engine.','scope':'Neutral face study only; no complete oral anatomy, expression dynamics or engine acceptance.'})
    key=base.add_key(body,'AFN23_NeutralLipCompression',P.astype(np.float64)+delta);key.value=weight;key.slider_min=0.;key.slider_max=1.;bpy.context.view_layer.update();Q=np.array(solid.data(body)[0],np.float64);expected=P.astype(np.float64)+delta*weight;error=float(np.linalg.norm(Q-expected,axis=1).max());assert error<5.e-7;assert controls()==before
    attachments=json.loads((R/'Evidence/character-female-next/r0010-eye-rim/c-spaced-lashes-lash-bindings.json').read_text())+json.loads((S/'aevrynd-female-next-r0018-c-brow-bindings.json').read_text())+json.loads((S/'aevrynd-female-next-r0014-root-bindings.json').read_text());maxAttachmentDelta=max(float(np.linalg.norm(delta[r['bodyVertices']]*weight,axis=1).max()) for r in attachments);assert maxAttachmentDelta==0.;bpy.context.scene['aevrynd_revision']='female-next-r0023-a';bpy.context.scene['aevrynd_release_state']='NEUTRAL_LIP_COMPRESSION_PENDING_SURFACE_VISUAL_GATES';bpy.context.scene['aevrynd_lip_weight']=weight;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));assert controls()==before;body=bpy.data.objects['AFN_R0008_Body'];actual=np.array(solid.data(body)[0],np.float64);assert np.linalg.norm(actual-expected,axis=1).max()<5.e-7;VV,TT,tree2=solid.data(body);afterRims=aperture(tree2,np.array(VV),TT)
    save('a-lip-margin-measurement.json',{'before':beforeRims,'after':afterRims,'fittedWeight':weight,'predictedWeightLimits':limits,'desiredMarginGapM':desired,'scope':'Frontal 27-section depth/aperture samples and linear native rim displacement estimates. Not a continuous, all-angle or full minimum-distance proof.'});save('a-build-verification.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(DST),'outputSha256':sha(DST),'targetData':inspection['cache'],'targetDataSha256':inspection['cacheSha256'],'key':'AFN23_NeutralLipCompression','weight':weight,'maximumEvaluatorErrorM':error,'maximumBodyMoveM':float(np.linalg.norm(delta*weight,axis=1).max()),'unrelatedHeadSkinHairRigLightMaterialControlExact':True,'maximumAttachmentBoundSkinMoveM':maxAttachmentDelta,'fileBytes':DST.stat().st_size,'wallSeconds':time.time()-started,'status':'REOPEN_AND_CONTROL_PASS_CONTACT_VISUAL_PENDING'});print('R0023_A_BUILD_PASS WEIGHT',weight,flush=True)
if __name__=='__main__':main()
