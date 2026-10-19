"""Second bounded architecture: same follicles/calibres, convergent brow flow.

Upper and lower rows converge along the brow axis. Shaft lengths use a bounded
anatomical design range rather than the first draft's short upward strokes.
No density/material/exposure increase. Conservative capsule contact rejection.
"""
import bpy,importlib.util,json,math,copy,shutil,time
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('b31',Path(__file__).with_name('build-female-next-r0031-native-brows.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
b=c.b;ROOT=c.E;E=ROOT/'b';E.mkdir(exist_ok=True);SRC=c.OUT;OUT=c.S/'aevrynd-female-next-r0031-b-convergent-brows.blend';BIND=c.S/'aevrynd-female-next-r0031-b-brow-bindings.json'
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    start=time.time();original_report=c.read('build-verification.json');assert b.sha(SRC)==original_report['outputSha256'];bindings=json.loads(c.BIND.read_text(encoding='utf8'));save('round-contract.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'candidate':'B,second and final in this round','diagnosis':'A uses short uniformly upward strokes; full head too pale and overly combed. Root count and calibrated fine shaft diameters are already plausible, so no pigment/density increase.','hypothesis':'Anatomically directed herringbone convergence and longer shafts restore natural brow body while retaining actual follicles, calibres, pigment and original head state.','held':['All candidate follicle/root surface metadata','Hair calibres and source material/color values','Body/eyes/skin/light/exposure/camera'],'references':[{'url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC5561712/','use':'Anatomy section: medial upright growth and central upper/downward lower/upward convergence.'},{'url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC6385518/','use':'Measured eyebrow shaft diameters around47-54micrometres in that studied population; not a universal prescribed size.'},{'url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC2884705/','use':'Eyebrow hair growth length context; B uses an engineered4.2-6.5mm groom range, not subject measurement.'}],'limits':{'maximumCandidatesThisRound':2,'maximumAdditionalFreeLiftM':.00036,'liftChoices':10,'maximumDroppedFollicleFraction':.10,'threads':4},'reject':['No full-head improvement, strong comb/stripe or unsupported thickening.','New body/eye/strand contacts.','More than10% fixed follicle paths cannot be placed within the lift bound.'],'clinicalScope':'References used only for visible anatomical modeling, no clinical recommendation or patient-specific claim.'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;b.E=E;c.a.q.b.E=E;c.a.E=E;controls=c.scene_controls();body=bpy.data.objects[b.BODY];V,T=b.evaluated(body,True);bt=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);accepted_hash=c.CapsuleHash();all_records=[];paths=[];radii=[];summary=[]
    for side,sign in (('L',1),('R',-1)):
        name=f'AFN31_{side}_BrowFibres';o=bpy.data.objects[name];oldcolors=np.empty(len(o.data.vertices)*4,dtype='f4');o.data.color_attributes['AFN31_FibreColor'].data.foreach_get('color',oldcolors);oldcolors=oldcolors.reshape(-1,4);records=[r for r in bindings['fibres'] if r['object']==name];vertices=[];faces=[];colors=[];dropped=[];lifts=[];lengths=[]
        for rec in records:
            t=rec['fieldParameter'];band=rec['rootBand'];root=rec['root'];point=np.array(root['surfacePointM']);length=float(np.clip(rec['lengthInputM']*(1.35 if t<.14 else 1.75),.0042,.0065));rr=np.array(rec['radiiM']);p0=np.array(rec['curvePointsM'][0]);n0=np.array(root['normal']);u=np.linspace(0,1,c.STATIONS);delta_t=length*.85/.0453;z_end=c.brow_center(min(.995,t+delta_t),sign)[1];axis_delta=z_end-c.brow_center(t,sign)[1];width=.0003+.00205*math.sin(math.pi*t)**.65;theta_convergent=math.atan2(axis_delta-band*width*.95,length*.85);head=max(0.,1-t/.18);theta=head*math.radians(72)+(1-head)*theta_convergent;bend=.10;P=[];N=[];valid=True
            for j,progress in enumerate(u):
                if j==0:P.append(p0);N.append(n0);continue
                xx=point[0]+sign*length*(math.sin(theta)-math.sin(theta-bend*progress))/bend;zz=point[2]+length*(math.cos(theta-bend*progress)-math.cos(theta))/bend;hit,normal,ti,d=bt.ray_cast(Vector((xx,-.35,zz)),Vector((0,1,0)),.5)
                if hit is None or normal.y>-.25:valid=False;break
                bc=c.barycentric(np.array(hit),V[T[ti]])
                if bc is None:valid=False;break
                skin=bc@V[T[ti]];n=np.array(normal);n/=np.linalg.norm(n);gap=root['rootNormalOffsetM']+(.00010 if band>0 else .00018)*math.sin(math.pi*progress);P.append(skin+n*gap);N.append(n)
            if not valid:dropped.append({'originalFibre':rec['fibre'],'reason':'skin ray'});continue
            P=np.array(P);N=np.array(N);chosen=None;chosen_lift=0
            for extra in np.linspace(0,.00036,10):
                proposed=P+N*(extra*(.70*np.sin(math.pi*u)+.30*u))[:,None];proposed[0]=p0
                if not accepted_hash.conflicts(proposed,rr):chosen=proposed;chosen_lift=float(extra);break
            if chosen is None:dropped.append({'originalFibre':rec['fibre'],'reason':'bounded capsule conflict'});continue
            points,tri=c.tube(chosen,rr,N);offset=len(vertices);vertices.extend(points.tolist());faces.extend(tuple(offset+i for i in f) for f in tri);colors.extend(oldcolors[rec['firstVertex']:rec['firstVertex']+c.VERTICES].tolist());new=copy.deepcopy(rec);new['originalFibreA']=rec['fibre'];new['fibre']=len(lifts);new['firstVertex']=offset;new['pathIndex']=len(paths);new['curvePointsM']=chosen.tolist();new['lengthInputM']=length;new['growthAngleRadians']=theta;new['additionalFreeLiftM']=chosen_lift;all_records.append(new);paths.append(chosen);radii.append(rr);accepted_hash.add(chosen,rr,len(paths)-1);lifts.append(chosen_lift);lengths.append(length)
        # Do not relax the ten-percent experimental retention gate. Preserve a
        # failed diagnostic candidate so its actual full-head result can still
        # be examined; it must remain explicitly rejected in the saved report.
        mat=o.data.materials[0];mesh=bpy.data.meshes.new(name+'_Convergent');mesh.from_pydata(vertices,[],faces);mesh.update();mesh.materials.append(mat);attr=mesh.color_attributes.new(name='AFN31_FibreColor',type='FLOAT_COLOR',domain='POINT');attr.data.foreach_set('color',np.array(colors,dtype='f4').ravel())
        for p in mesh.polygons:p.use_smooth=True
        o.data=mesh;o['AFN31_root_bindings']=BIND.name;row={'object':name,'fibres':len(lifts),'originalFollicles':len(records),'dropped':dropped,'vertices':len(vertices),'triangles':len(faces),'maximumExtraFreeLiftM':max(lifts),'lengthRangeM':[min(lengths),max(lengths)]};summary.append(row);print('R31B_BROW',json.dumps(row),flush=True)
    assert c.scene_controls()==controls
    retention_failed=any(len(r['dropped'])/r['originalFollicles']>.10 for r in summary)
    bindings['fibres']=all_records;bindings['parentGroomSource']=str(SRC);bindings['parentGroomSha256']=b.sha(SRC);bindings['method']='Subset of same actual skin follicles/calibres/colors; herringbone flow and bounded contact-separated free lengths.';BIND.write_text(json.dumps(bindings,separators=(',',':'))+'\n',encoding='utf8');cache=c.S/'aevrynd-female-next-r0031-b-brow-curves.npz';np.savez_compressed(cache,positions=np.array(paths),radii=np.array(radii));b.camera('face');s['AFN31_status']='REJECTED_FOLLICLE_RETENTION_DIAGNOSTIC' if retention_failed else 'CONVERGENT_NATIVE_BROW_STATIC_REVIEW';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('build-verification.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'baseHeadSource':str(c.SRC),'baseHeadSourceSha256':b.sha(c.SRC),'output':str(OUT),'outputSha256':b.sha(OUT),'bindings':str(BIND),'bindingsSha256':b.sha(BIND),'curveCache':str(cache),'originalControls':controls,'originalBodyEyesSkinStageExact':True,'brows':summary,'radiusM':[.000002,.000030],'minimumInterstrandCapsuleGapDesignM':.000006,'method':bindings['method'],'decision':'REJECT_FOLLICLE_RETENTION_BOUND' if retention_failed else 'PENDING_VISUAL_AND_SAVED_GATE','seconds':time.time()-start,'limits':['Static source only; no facial rig/deforming binding or engine acceptance.','More than ten percent rejected source follicles is a failed experimental control, never silently waived.']})
    before=c.read('before-renders.json')
    for r in before['rows']:
        dest=E/Path(r['path']).name;shutil.copyfile(r['path'],dest);r['path']=str(dest)
    save('before-renders.json',before);shutil.copyfile(ROOT/'before-eyes.png',E/'before-eyes.png');c.a.q.render('after');c.a.closeup('after');print('R0031_B_BUILD_DONE',flush=True)
if __name__=='__main__':main()
