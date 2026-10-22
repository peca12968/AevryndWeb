"""Direct current-world rest sculpt, fixed root births, explicit guide correspondence.
One complete displayed candidate; no foreign rest surface deformation or random generator.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time,datetime
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0172-current-world-comb';OUT=C/'assets-source/aevrynd-character/female-next/r0172-source/aevrynd-female-next-r0172-a-current-world-comb.blend'
sp=importlib.util.spec_from_file_location('r172base',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2)+'\n').encode())
def attr(d,n,typ,dom,prop,v):d.attributes.new(n,typ,dom).data.foreach_set(prop,np.asarray(v).ravel())
def spline(P):
    # Artist control strokes sampled as a smooth path, then at equal arc distance.
    P=np.asarray(P,float);Q=np.vstack((P[0],P,P[-1]));result=[]
    for i in range(len(P)-1):
        p0,p1,p2,p3=Q[i:i+4]
        for t in np.linspace(0,1,12,endpoint=False):result.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t**3))
    result=np.vstack((result,P[-1]));arc=np.r_[0,np.linalg.norm(np.diff(result,axis=0),axis=1).cumsum()];out=np.stack([np.interp(np.linspace(0,arc[-1],16),arc,result[:,j]) for j in range(3)],axis=1);out[0]=P[0];return out
def comb(root,normal,gid):
    # Explicit current-woman front/crown/temple/nape shaping strokes, metres.
    # Root remains the original actual Skin triangle/barycentric constraint.
    x,y,z=map(float,root);side=1 if x>=0 else -1;tip=1.300+.007*np.sin(gid*2.39996);spread=.003*np.sin(gid*1.618)
    first=root+normal*.003
    if y<-.035 and z>1.53:
        region='front_and_part';xx=max(abs(x)+.012,.043)
        control=[root,first,[side*xx,min(y+.007,-.055),max(z+.006,1.578)],[side*.072,-.052,1.555],[side*.087,-.028,1.505],[side*(.095+spread),-.002,1.425],[side*(.091+spread),.015,1.345],[side*(.080+spread),.023,tip]]
    elif z>1.535 and y<.02:
        region='crown_side';xx=max(abs(x)+.013,.042)
        control=[root,first,[side*xx,y+.007,max(z+.008,1.577)],[side*.075,y+.017,1.548],[side*.089,.025,1.485],[side*(.094+spread),.040,1.400],[side*(.083+spread),.048,tip]]
    elif y>=.02 or (z<1.51 and abs(x)<.045):
        region='occiput_and_nape';xx=x*1.08;dy=max(y+.013,.069)
        control=[root,first,[xx,dy,min(z-.012,1.535)],[xx*1.11,dy+.014,min(z-.046,1.485)],[xx*1.10+spread,dy+.018,min(z-.100,1.405)],[xx*.96+spread,dy+.010,tip-.008]]
    else:
        region='temple_and_ear';xx=max(abs(x)+.013,.079)
        control=[root,first,[side*xx,y+.006,z-.012],[side*.093,max(y+.025,-.015),min(z-.055,1.475)],[side*(.097+spread),.020,min(z-.118,1.400)],[side*(.084+spread),.034,tip]]
    return spline(control),region,np.asarray(control)
def main():
    tick=time.time();timing=json.loads((E/'before.json').read_text());assert not OUT.exists() and a.a.sha(Path(timing['source']))==timing['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=timing['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};W,T=a.geometry(skin);line=np.load(E.parent/'r0171-actual-scalp-chart/actual-scalp-groom-lineage.npz');ids=line['parentRootVertexIDs'];gT=line['carrierCurrentTriangles'][ids];gBC=line['carrierCurrentBarycentric'][ids];gRoot=(W[gT]*gBC[:,:,None]).sum(1);B=W[gT];ax=B[:,1]-B[:,0];ax/=np.linalg.norm(ax,axis=1,keepdims=True);az=np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]);az/=np.linalg.norm(az,axis=1,keepdims=True);ay=np.cross(az,ax);basis=np.stack((ax,ay,az),axis=2)
    oldGuide=bpy.data.objects['AFN171_EDITABLE_ORIGINAL_POSED_GUIDES'];oldWorld,oldOffsets=m.curveworld(oldGuide);assert len(oldOffsets)==252
    G=[];regions=[];strokes=[]
    for i,root in enumerate(gRoot):
        p,region,control=comb(root,az[i],i);G.append(p);regions.append(region);strokes.append({'actualGuideID':i,'region':region,'actualRootTriangle':gT[i].tolist(),'rootBarycentric':gBC[i].tolist(),'authoredWorldStroke':control.tolist()})
    G=np.asarray(G,'f4');assert np.isfinite(G).all() and np.max(np.linalg.norm(G[:,0]-gRoot,axis=1))<3e-6
    gd=bpy.data.hair_curves.new('AFN172_DIRECT_CURRENT_WORLD_REST_GUIDES_DATA');gd.add_curves([16]*252);gd.position_data.foreach_set('vector',G.ravel());attr(gd,'AFN172_GUIDE_ID','INT','CURVE','value',np.arange(252,dtype='i4'));go=bpy.data.objects.new('AFN172_DIRECT_CURRENT_WORLD_EDITABLE_GUIDES',gd);s.collection.objects.link(go);go.hide_render=True;go.hide_set(True);local=np.einsum('bni,bij->bnj',G-gRoot[:,None],basis);h.bind(go,skin,gT,gBC,local,G)
    roots=line['fixedRootWorld'];N=len(roots);assert N==10191;delta=gRoot[None]-roots[:,None];distance=np.linalg.norm(delta,axis=2);distance[(gRoot[:,0]>=0)[None]!=(roots[:,0]>=0)[:,None]]=1e6;nearest=np.argsort(distance,axis=1)[:,:4];dist=np.take_along_axis(distance,nearest,axis=1);weights=1/np.maximum(dist,.0002)**2;weights/=weights.sum(1,keepdims=True);P=roots[:,None]+np.einsum('bi,bink->bnk',weights,(G-gRoot[:,None])[nearest]);P=P.astype('f4');P[:,0]=roots;assert np.isfinite(P).all()
    hd=bpy.data.hair_curves.new('AFN172_FIXED_BIRTH_EXPLICIT_DISPLAY_CURVES_DATA');hd.add_curves([16]*N);hd.position_data.foreach_set('vector',P.ravel());attr(hd,'radius','FLOAT','POINT','value',np.tile(np.linspace(.0001,0,16,dtype='f4'),N));attr(hd,'AFN172_BIRTH_ID','INT','CURVE','value',np.arange(N,dtype='i4'));attr(hd,'AFN172_ROOT_SAMPLE','INT','POINT','value',np.repeat(np.arange(N,dtype='i4'),16));attr(hd,'AFN172_REST_WORLD','FLOAT_VECTOR','POINT','vector',P.reshape(-1,3))
    for k in range(4):
        attr(hd,f'AFN172_GUIDE_POINT_{k}','INT','POINT','value',(nearest[:,k,None]*16+np.arange(16)[None]).astype('i4').ravel());attr(hd,f'AFN172_GUIDE_ROOT_{k}','INT','POINT','value',np.repeat(nearest[:,k]*16,16).astype('i4'));attr(hd,f'AFN172_GUIDE_WEIGHT_{k}','FLOAT','POINT','value',np.repeat(weights[:,k],16).astype('f4'))
    hair=bpy.data.objects.new('AFN172_ACTUAL_WORLD_COMBED_FIXED_BIRTH_GROOM',hd);s.collection.objects.link(hair);hd.materials.append(bpy.data.materials['AFN169_NATIVE_FIBRE_SAME_REFERENCE_COLOR']);rootOb=bpy.data.objects['AFN171_FIXED_ACTUAL_SKIN_ROOTS'];group=bpy.data.node_groups.new('AFN172_EXPLICIT_FOUR_GUIDE_FIXED_BIRTH_DEFORMATION','GeometryNodeTree');group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');n=group.nodes;L=group.links;inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');pos=n.new('GeometryNodeInputPosition')
    def named(name,typ='FLOAT_VECTOR'):
        x=n.new('GeometryNodeInputNamedAttribute');x.data_type=typ;x.inputs['Name'].default_value=name;return x.outputs['Attribute']
    def info(ob):
        x=n.new('GeometryNodeObjectInfo');x.transform_space='RELATIVE';x.inputs['Object'].default_value=ob;return x.outputs['Geometry']
    def sample(geom,index):
        x=n.new('GeometryNodeSampleIndex');x.data_type='FLOAT_VECTOR';x.domain='POINT';x.clamp=False;L.new(geom,x.inputs['Geometry']);L.new(pos.outputs[0],x.inputs['Value']);L.new(index,x.inputs['Index']);return x.outputs['Value']
    def vec(op,*v):
        x=n.new('ShaderNodeVectorMath');x.operation=op
        for j,q in enumerate(v):L.new(q,x.inputs[j])
        return x.outputs[0]
    def scale(v,w):
        x=n.new('ShaderNodeVectorMath');x.operation='SCALE';L.new(v,x.inputs[0]);L.new(w,x.inputs['Scale']);return x.outputs[0]
    guideGeom=info(go);rootGeom=info(rootOb);position=sample(rootGeom,named('AFN172_ROOT_SAMPLE','INT'))
    for k in range(4):position=vec('ADD',position,scale(vec('SUBTRACT',sample(guideGeom,named(f'AFN172_GUIDE_POINT_{k}','INT')),sample(guideGeom,named(f'AFN172_GUIDE_ROOT_{k}','INT'))),named(f'AFN172_GUIDE_WEIGHT_{k}','FLOAT')))
    position=vec('ADD',position,vec('SUBTRACT',pos.outputs[0],named('AFN172_REST_WORLD')));setp=n.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setp.inputs['Geometry']);L.new(position,setp.inputs['Position']);L.new(setp.outputs['Geometry'],out.inputs['Geometry']);hair.modifiers.new('AFN172_FIXED_BIRTH_NATIVE_DISPLAY_FROM_ACTUAL_GUIDES','NODES').node_group=group
    for oldName in ['AFN171_ACTUAL_SURFACE_ROOTED_NATIVE_GROOM',a.FIXED[1]]:bpy.data.objects[oldName].hide_render=True;bpy.data.objects[oldName].hide_set(True)
    bpy.context.view_layer.update();actual,offset=m.curveworld(hair);error=float(np.linalg.norm(actual-P.reshape(-1,3),axis=1).max());assert error<3e-6,error;assert protected=={name:a.rawsig(bpy.data.objects[name]) for name in protected}
    save('direct-current-world-rest-authoring.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':timing['startedUTC'],'changedFailedPremise':'Directly sculpt all252 CURRENT-world guide paths at their proven actual Skin roots, replacing erroneous source/rest tangent flow. Display samples explicitly identified guide points/root points and fixed birth roots; no native Interpolate Curves up-vector rotation, random child generation or output-index identity assignment. Not a new foreign chart/whole-groom transform.','actualSkin':skin.name,'actualGuides':go.name,'actualHair':hair.name,'regions':{q:regions.count(q) for q in set(regions)},'preserved252RootConstraints':True,'guide0And61Before':oldWorld.reshape(252,16,3)[[0,61]].tolist(),'guide0And61After':G[[0,61]].tolist(),'allGuideControlStrokes':strokes,'same10191BirthRootsAndFixedMaterialRadiusAs171':True,'noDensityRadiusMaterialSweep':True,'nativeDisplayedConstructionMaximumErrorM':error,'sourceChartUsedOnlyForExistingRootOwnershipNotNewFreeShape':True})
    np.savez_compressed(E/'current-world-comb-lineage.npz',guideRootTriangles=gT,guideRootBarycentric=gBC,guideWorld=G,guideLocal=local.astype('f4'),fixedRootTriangles=line['fixedRootTriangles'],fixedRootBarycentric=line['fixedRootBarycentric'],fixedRootWorld=roots,childGuideIndices=nearest.astype('i4'),childGuideWeights=weights.astype('f4'),actualScalpFaces=line['actualScalpFaces'])
    save('world-comb-construction.json',{'nativeCurves':N,'points':len(actual),'guideCurves':252,'allBirthRootMaximumErrorM':float(np.linalg.norm(actual[offset]-roots,axis=1).max()),'nativeWorldMaximumConstructionErrorM':error,'worldGeometryHash':a.a.hasharray(actual),'sameMaterialRadiusCountAs171':True,'explicitPointAndRootCorrespondence':True,'guideTipsHigherThanRoots':int((G[:,-1,2]>G[:,0,2]).sum()),'originalUnchangedSourceGuideRawDataPreservedHidden':True,'noClaimOfNaturalHairDynamicsFiniteContactsOrRuntime':True})
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True)
    save('a-build-summary.json',{'source':timing['source'],'output':str(OUT),'engineAlias':str(R/'engine/assets/characters/female-next/source/r0172-source'/OUT.name),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':'AFN138_ACTUAL_CURRENT_GAZE_RIG','actualHair':hair.name,'actualGuides':go.name,'actualRoots':rootOb.name,'retainedSourceHair':a.FIXED[1],'nativeStrands':N,'points':len(actual),'fullNativeGroomCandidate':True,'unaccepted':True,'secondsBeforePreview':time.time()-tick});assert OUT.stat().st_size<timing['sourceBudgetBytes'];a.b.u.v.E=E;views=[]
    for view in ['face','body-face','profile','back','oblique']:
        ctl=a.b.u.v.image('a-current-world-comb',view);ctl.update(frame=1,actualHair=hair.name,hairTypeAtActualCapture=s.render.hair_type,actualSamplesAtCapture=s.cycles.samples,actualResolutionAtCapture=[s.render.resolution_x,s.render.resolution_y]);views.append(ctl);save('current-world-comb-preview-controls.json',views)
    print('R172_CURRENT_WORLD_COMBED_FIXED_BIRTH_COMPLETE_WOMAN_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
