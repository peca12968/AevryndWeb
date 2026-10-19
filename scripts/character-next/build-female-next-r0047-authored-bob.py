"""Integrate a single explicitly CC0 artist-authored hairstyle on same body.

Own MHCLO reader + source-skin registration. Cards are an aggregate rendering
representation, not individually simulated fibres. Exact current body/optic
contacts are tested independently; fitting data is never contact evidence.
"""
import bpy,importlib.util,json,time,hashlib,shutil
from pathlib import Path
import numpy as np
from mathutils import Vector
sp=importlib.util.spec_from_file_location('bob47base',Path(__file__).with_name('inspect-female-next-r0043-ocular-junction.py'));i=importlib.util.module_from_spec(sp);sp.loader.exec_module(i)
b=i.b;f=i.f;v=i.v;R=b.R;S=b.S;E=R/'Evidence/character-female-next/r0047-anatomical-hair';E.mkdir(exist_ok=True);REF=R/'Reference/character/makehuman-core-bob02-cc0';ASSET=S/'cc0-hair/bob02';SRC=S/'aevrynd-female-next-r0042-b-shadow-quality-review.blend';OUT=S/'aevrynd-female-next-r0047-a-cc0-authored-bob-fit.blend'
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def obj(path):
    V=[];UV=[];faces=[];tfaces=[]
    for line in path.read_text(encoding='utf8').splitlines():
        p=line.split()
        if not p:continue
        if p[0]=='v':V.append(list(map(float,p[1:4])))
        elif p[0]=='vt':UV.append(list(map(float,p[1:3])))
        elif p[0]=='f':
            z=[q.split('/') for q in p[1:]];faces.append([int(q[0])-1 for q in z]);tfaces.append([int(q[1])-1 if len(q)>1 and q[1] else -1 for q in z])
    return np.array(V,dtype='f8'),np.array(UV,dtype='f8'),faces,tfaces
def mhclo(path):
    text=path.read_text(encoding='utf8');assert 'explicitly released as CC0' in text;rows=[];scales={};active=False
    for line in text.splitlines():
        p=line.split()
        if not p or p[0].startswith('#'):continue
        if p[0] in ('x_scale','y_scale','z_scale'):scales[p[0][0]]=(int(p[1]),int(p[2]),float(p[3]))
        elif p[0]=='verts':active=True
        elif active:
            if not p[0].isdigit():break
            if len(p)==1:rows.append(([int(p[0])]*3,[1.,0.,0.],[0.,0.,0.]))
            else:assert len(p)==9,p;rows.append((list(map(int,p[:3])),list(map(float,p[3:6])),list(map(float,p[6:9]))))
    ids=np.array([x[0] for x in rows],dtype='i4');w=np.array([x[1]for x in rows]);off=np.array([x[2]for x in rows]);assert np.max(abs(w.sum(1)-1))<3e-5;return ids,w,off,scales
def yup(P):return P[:,[0,2,1]]*np.array((.1,-.1,.1))
def fit(P,ids,w,off,scales):
    axis={'x':0,'y':2,'z':1};scale={name:abs(P[x,axis[name]]-P[y,axis[name]])/(d*.1) for name,(x,y,d) in scales.items()};delta=off[:,[0,2,1]]*np.array((.1*scale['x'],-.1*scale['z'],.1*scale['y']));return np.einsum('ni,nij->nj',w,P[ids])+delta,scale
def fitting_oracle(cases,ids,w,offset,scales):
    # Independent installed production-tool call, never copied into runtime.
    import bl_ext.user_default.mpfb as mpfb
    mpfb.MPFB_CONTEXTUAL_INFORMATION={'__package__':str(mpfb.__package__),'__package_short__':str(mpfb.__package__).split('.')[-1],'__file__':str(mpfb.__file__)}
    prefs={'mpfb_shelf_label':'MPFB','mpfb_user_data':'','mpfb_second_root':'','mh_user_data':'','mh_auto_user_data':False};mpfb.get_preference=lambda n:prefs.get(n)
    from bl_ext.user_default.mpfb.services import ClothesService
    from bl_ext.user_default.mpfb.entities.objectproperties import GeneralObjectProperties
    from bl_ext.user_default.mpfb.entities.clothes.mhclo import Mhclo
    rows=[]
    for label,P in cases:
        bm=bpy.data.meshes.new('AFN47_ORACLE_BODY');bm.from_pydata(P.tolist(),[],[]);human=bpy.data.objects.new(bm.name,bm);bpy.context.scene.collection.objects.link(human)
        GeneralObjectProperties.set_value('object_type','Basemesh',entity_reference=human);GeneralObjectProperties.set_value('scale_factor',.1,entity_reference=human)
        cm=bpy.data.meshes.new('AFN47_ORACLE_CARDS');cm.from_pydata(np.zeros((len(ids),3)).tolist(),[],[]);cards=bpy.data.objects.new(cm.name,cm);bpy.context.scene.collection.objects.link(cards)
        mh=Mhclo();mh.load(str(ASSET/'bob02.mhclo'));mh.clothes=cards;ClothesService.fit_clothes_to_human(cards,human,mh,set_parent=False)
        actual=np.empty(len(ids)*3,dtype='f4');cm.vertices.foreach_get('co',actual);expected,_=fit(P,ids,w,offset,scales);err=np.linalg.norm(actual.reshape(-1,3)-expected,axis=1)
        row={'input':label,'vertices':len(ids),'maxDifferenceM':float(err.max()),'p99DifferenceM':float(np.percentile(err,99)),'toleranceM':1e-6,'passed':bool(err.max()<1e-6)};rows.append(row);assert row['passed'],row
        bpy.data.objects.remove(cards,do_unlink=True);bpy.data.objects.remove(human,do_unlink=True);bpy.data.meshes.remove(cm);bpy.data.meshes.remove(bm)
    save('independent-fitting-oracle.json',{'scope':'Own affine fitter vs installed MPFB ClothesService on identical input coordinates. This proves parser/scale implementation, not target-head fit, collision or appearance. No GPL tool implementation copied into engine.','rows':rows});return rows
def main():
    tick=time.time();assert b.sha(SRC)=='d62c180a5af61f6f8d800926b101738c89a8fbe7785fe1054fd655fd018824da';prov=json.loads((REF/'PROVENANCE.json').read_text());assert prov['asset']=='bob02'
    for row in prov['files']:assert b.sha(REF/row['file'])==row['sha256']
    for name in ['bob02.mhclo','bob02.obj','bob02.mhmat']:assert 'explicitly released as CC0' in (REF/name).read_text(encoding='utf8')
    ASSET.mkdir(parents=True,exist_ok=True)
    for p in REF.iterdir():
        if p.is_file():shutil.copy2(p,ASSET/p.name)
    originalAsset,uv,faces,uvfaces=obj(ASSET/'bob02.obj');ids,w,offset,scales=mhclo(ASSET/'bob02.mhclo');assert len(ids)==len(originalAsset)
    basePath=Path(r'C:\Users\USER\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\user_default\mpfb\data\3dobjs\base.obj');base,_,_,_=obj(basePath);base=yup(base);default,defaultScale=fit(base,ids,w,offset,scales);defaultError=np.linalg.norm(default-yup(originalAsset),axis=1)
    ref=np.load(R/'Evidence/character-female-next/r0045-closed-lid-topology/b-cc0-authored-closed-reference.npz');P=ref['restWorld'];visible=np.unique(ref['triangles']);cs=(ref['eyeCenterL'].astype('f8')+ref['eyeCenterR'].astype('f8'))*.5
    fitting_oracle([('Unmodified installed hm08 default mesh',base),('Previously generated CC0 female reference',P)],ids,w,offset,scales)
    save('prior-test-assumption-reconciliation.json',{'previousAssertion':'Expect original authored bob OBJ to reproduce on raw neutral hm08 base within0.2mm','observedDifferenceM':float(defaultError.max()),'reasonNotUsedAsOracle':'The original authored mesh is not established to share this default macro body/rest pose. Scale anchor spans differ from the MHCLO authoring spans. Different input shapes cannot establish a fitter error.','replacementEvidence':'Independent installed MPFB fitting API compared on identical input vertices; tolerance1micrometre, no tolerance relaxation.','decision':'Withdraw unsupported original-rest equality requirement; retain original asset bytes and observed difference; validate actual target fit/appearance independently.'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=4;before=f.state();body=bpy.data.objects[b.BODY];V,T=b.evaluated(body,True);tree=i.i.tree(V,T);ct=np.mean([i.i.FITS[x]['centerM']for x in ('L','R')],axis=0);sx=(i.i.FITS['L']['centerM'][0]-i.i.FITS['R']['centerM'][0])/(ref['eyeCenterL'][0]-ref['eyeCenterR'][0]);sz=(float(V[:,2].max())-ct[2])/(float(P[visible,2].max())-cs[2]);registration=np.array((sx,(sx+sz)*.5,sz));mapped=P.copy();support=sorted(set(ids.ravel())|{n for x,y,d in scales.values() for n in (x,y)});mapping=[]
    for index in support:
        expected=(P[index]-cs)*registration+ct;hit,n,tid,dist=tree.find_nearest(Vector(expected));mapped[index]=hit;mapping.append({'sourceVertex':int(index),'targetBodyTriangle':int(tid),'targetSurfacePointM':list(hit),'registrationProjectionDistanceM':float(dist),'referenceKind':'Source native body support, not a follicle or physical collision proxy'})
    fitted,axisScale=fit(mapped,ids,w,offset,scales);save('round-contract.json',{'revision':'female-next-r0047-a','previousGoalTurnClassification':'progress: two complete own grooms rejected and archived6a423e3; no appearance gain','source':str(SRC),'sourceSha256':b.sha(SRC),'mainDefects':['Hat/sheet hair without credible scalp coverage/layering','Staring eyes','Flat skin'],'chosenDefect':'Complete hairstyle/hairline and anatomical source-body fitting','planChangeFromContinuation':'CC0 helper-hair boundsZ0.9625..1.5570 on reference: long-hair envelope, not a scalp follicle region; do not treat it as scalp mask. Use explicitly CC0 artist hairstyle and its native body-surface fitting correspondence.','hypothesis':'Artist-authored asymmetric hairline, fringe and layered bob geometry with existing UV/strand texture can provide a credible complete form on the same owned head, avoiding repeated mathematical shell generators','method':'Own MHCLO affine fitting-data reader, validate against installed MPFB on identical input shapes within1micrometre, then register source native body support to current actual skin and apply authored offsets/axis scales. Imported model is aggregate textured hair-card mesh, not individual fibres or a new paid tool.','candidateCount':1,'cheapTest':'Independent identical-input fitting oracle, complete fixed-stage head/body/multiangle visual integration, raw actual hair/body8optics triangles before costly motion work','reject':['Invalid source/license or independent fitter disagreement','Unusable full-head wig/card/shell appearance','Body/optics visible penetration or unqualified contact','Changed body/skin/eyes/lighting'],'resources':{'startUTC':'2026-10-19 15:47:08 UTC','checkpointUTC':'2026-10-19 16:32:08 UTC','threads':4,'heavyJobsAtOnce':1,'assetDownloadBytes':prov['downloadedRangeBytes'],'entire267MBPackNotDownloaded':True},'sourceAsset':prov,'scope':'Static full-character hairstyle integration only. No per-fibre physiology,self collision,hair dynamics,engine fidelity/performance or female acceptance.'})
    mesh=bpy.data.meshes.new('AFN47_CC0_Bob02_AuthoredCards');mesh.from_pydata(fitted.tolist(),[],faces);mesh.update();hair=bpy.data.objects.new(mesh.name,mesh);s.collection.objects.link(hair);uvLayer=mesh.uv_layers.new(name='UVMap')
    for poly,ufs in zip(mesh.polygons,uvfaces):
        poly.use_smooth=True
        for loop,ui in zip(poly.loop_indices,ufs):assert ui>=0;uvLayer.data[loop].uv=uv[ui]
    image=bpy.data.images.load(str(ASSET/'bob02_diffuse.png'),check_existing=True);image.alpha_mode='STRAIGHT';image.pack();mat=bpy.data.materials.new('AFN47_Bob02_CC0_TextureApproximation');mat.use_nodes=True;mat.surface_render_method='DITHERED';mat.use_backface_culling=False;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.48;bs.inputs['Specular IOR Level'].default_value=.24;bs.inputs['Anisotropic'].default_value=.5;tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Linear';tint=mat.node_tree.nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1.;tint.inputs[2].default_value=(.34,.17,.075,1);mat.node_tree.links.new(tex.outputs['Color'],tint.inputs[1]);mat.node_tree.links.new(tint.outputs[0],bs.inputs['Base Color']);mat.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);mesh.materials.append(mat)
    original=bpy.data.objects['AFN33_C_BODY_BOUND_FIBRES'];original.hide_render=True;original.hide_set(True);hair['aevrynd_layer']='AGGREGATE_TEXTURED_HAIR_CARDS';hair['asset_license']='CC0';hair['source']='MakeHuman system bob02; original exact files and source headers retained';hair['scope']='Static authored mesh-card representation. Not12000individual fibres or accepted hair physics. Approximate Principled material; original litsphere shader is not reproduced.'
    bpy.context.view_layer.update();H,HT=b.evaluated(hair,True);ht=i.i.tree(H,HT);bodyPairs=ht.overlap(tree);optics={}
    for side in ('L','R'):
        for part in ('Sclera','Cornea','Iris','Pupil'):
            name=f'AFN30_{side}_{part}';pv,pt=b.evaluated(bpy.data.objects[name],True);optics[name]=len(ht.overlap(i.i.tree(pv,pt)))
    vertexDist=[tree.find_nearest(Vector(x))[3] for x in H];after=f.state();assert all(after['meshes'][name]==row for name,row in before['meshes'].items());assert all(after['materials'][name]==row for name,row in before['materials'].items());assert after['skinFields']==before['skinFields'] and after['stage']==before['stage'];assert after['curves']==before['curves'];s['AFN47_status']='CC0_AUTHORED_COMPLETE_HAIR_FIT_UNQUALIFIED';b.camera('face');s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build-summary.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),'vertices':len(H),'triangles':len(HT),'sourceUVPreserved':True,'sourceNativePolygonTopologyPreserved':True,'originalObjVsDifferentDefaultBaseDifferenceM':float(defaultError.max()),'originalBaseOffsetScales':defaultScale,'registrationAxisScale':registration.tolist(),'targetOffsetScales':axisScale,'currentBodySkinOpticsMaterialsLightingExact':True,'fallbackOwnedGroomDataExact':True,'rawHairBodyTrianglePairs':len(bodyPairs),'bodyPairExamples':[[int(x),int(y)]for x,y in bodyPairs[:30]],'actualHairOpticsTrianglePairs':optics,'minimumVertexSampleUnsignedBodyGapM':float(min(vertexDist)),'gapScope':'Vertex-sampled unsigned surface distance, not a global minimum or thickness certificate','materialApproximation':{'source':'CC0 RGBA texture and UV preserved, packed','shader':'Own Principled BSDF approximation, not original MakeHuman litsphere shader','linearTint':[.34,.17,.075],'roughness':.48,'specularIORLevel':.24,'anisotropicIOR':.5,'transparency':'DITHERED,linear filtering,STRAIGHT alpha,double sided','representation':'Aggregate rendering cards; no single-fibre self/dynamics inference'},'seconds':time.time()-tick});save('a-current-body-fit-correspondence.json',{'sourceBase':str(basePath),'sourceBaseSha256':b.sha(basePath),'referenceCurrentFemale':str(R/'Evidence/character-female-next/r0045-closed-lid-topology/b-cc0-authored-closed-reference.npz'),'sourceDataLicense':'CC0 core assets, no runtime source code copied','supportMapping':mapping,'mhcloVertexSourceIndices':ids.tolist(),'affineWeights':w.tolist(),'authoredOffsetsOriginalUnits':offset.tolist(),'note':'Some authored affine weights are negative; these are fitting coordinates, not physical root barycentric bindings. Actual post-fit contacts tested independently.'});f.E=E;f.render('a-after',('face','oblique','profile'));i.ch.review.extras('a-after',E);print('R47_AUTHORED_BOB_READY',len(H),len(HT),'bodyPairs',len(bodyPairs),'optics',optics,time.time()-tick,flush=True)
if __name__=='__main__':main()
