"""Actual current scalp root bands and directly authored primary clump volumes.
Coarse form stage of one concept; no render children before whole form review.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time,datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0188-current-primary-clumps';OUT=C/'assets-source/aevrynd-character/female-next/r0188-source/aevrynd-female-next-r0188-coarse-current-primary-clumps.blend'
sp=importlib.util.spec_from_file_location('r169',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def save(n,q):(E/n).write_bytes((json.dumps(q,indent=2)+'\n').encode())
def unit(v):return v/max(np.linalg.norm(v),1e-15)
# Independently authored current-world root seeds and complete outer shapes.
# Root bands are replaced by actual Skin anchors, not these approximate seeds.
STROKES=[
('front-L',[[-.004,-.087,1.551],[-.032,-.091,1.570],[-.060,-.084,1.558],[-.083,-.077,1.533],[-.102,-.070,1.494],[-.110,-.064,1.447],[-.104,-.065,1.399],[-.088,-.073,1.364]],.011,.0032),
('topfront-L',[[-.004,-.066,1.563],[-.035,-.067,1.581],[-.064,-.059,1.564],[-.088,-.046,1.533],[-.105,-.037,1.488],[-.115,-.037,1.441],[-.107,-.046,1.393],[-.091,-.057,1.361]],.013,.0038),
('crown-L',[[-.004,-.042,1.570],[-.037,-.038,1.583],[-.070,-.024,1.563],[-.092,-.009,1.526],[-.110,.004,1.482],[-.117,.007,1.436],[-.106,-.004,1.389],[-.090,-.020,1.358]],.0135,.004),
('toprear-L',[[-.004,-.018,1.568],[-.034,-.006,1.580],[-.069,.014,1.554],[-.095,.034,1.516],[-.111,.046,1.472],[-.115,.049,1.429],[-.100,.037,1.386],[-.085,.021,1.354]],.014,.0041),
('rearpart-L',[[-.004,.006,1.559],[-.031,.029,1.573],[-.063,.052,1.548],[-.088,.071,1.509],[-.103,.082,1.466],[-.101,.086,1.420],[-.087,.076,1.380],[-.072,.059,1.352]],.0135,.004),
('upperocciput-L',[[-.004,.029,1.543],[-.023,.053,1.560],[-.048,.078,1.536],[-.072,.096,1.498],[-.084,.107,1.453],[-.081,.110,1.412],[-.067,.094,1.375],[-.054,.078,1.348]],.013,.0038),
('front-R',[[.004,-.085,1.552],[.034,-.086,1.573],[.064,-.077,1.556],[.088,-.065,1.525],[.106,-.057,1.484],[.113,-.055,1.440],[.104,-.060,1.392],[.087,-.070,1.362]],.0115,.0033),
('topfront-R',[[.004,-.062,1.565],[.038,-.059,1.580],[.069,-.047,1.560],[.093,-.029,1.524],[.110,-.015,1.478],[.118,-.015,1.432],[.109,-.028,1.388],[.091,-.044,1.358]],.013,.0038),
('crown-R',[[.004,-.038,1.570],[.038,-.027,1.583],[.071,-.008,1.557],[.097,.015,1.517],[.115,.030,1.472],[.118,.034,1.426],[.104,.020,1.383],[.086,.004,1.353]],.014,.0042),
('toprear-R',[[.004,-.013,1.568],[.035,.006,1.577],[.068,.030,1.549],[.094,.052,1.507],[.111,.065,1.463],[.111,.069,1.419],[.096,.055,1.377],[.078,.039,1.350]],.014,.004),
('rearpart-R',[[.004,.011,1.557],[.029,.037,1.569],[.060,.061,1.542],[.085,.084,1.500],[.099,.094,1.456],[.094,.100,1.412],[.077,.082,1.372],[.061,.065,1.347]],.013,.0038),
('upperocciput-R',[[.004,.033,1.539],[.022,.059,1.553],[.045,.084,1.527],[.067,.103,1.485],[.078,.114,1.443],[.069,.113,1.402],[.054,.097,1.368],[.041,.081,1.345]],.013,.0037),
('temple-L',[[-.050,-.073,1.535],[-.072,-.077,1.538],[-.090,-.075,1.513],[-.105,-.067,1.477],[-.111,-.058,1.433],[-.102,-.061,1.390],[-.087,-.071,1.361]],.010,.003),
('parietal-L',[[-.067,-.034,1.522],[-.085,-.029,1.525],[-.101,-.015,1.497],[-.114,-.003,1.456],[-.115,-.006,1.414],[-.102,-.020,1.376],[-.088,-.034,1.352]],.012,.0035),
('sideback-L',[[-.067,.017,1.500],[-.084,.034,1.505],[-.101,.051,1.478],[-.110,.064,1.438],[-.105,.057,1.399],[-.090,.042,1.365],[-.077,.029,1.347]],.012,.0033),
('temple-R',[[.050,-.069,1.537],[.075,-.069,1.538],[.094,-.062,1.510],[.108,-.050,1.470],[.112,-.045,1.428],[.102,-.051,1.386],[.087,-.064,1.359]],.010,.003),
('parietal-R',[[.068,-.029,1.520],[.087,-.019,1.524],[.105,-.002,1.494],[.116,.013,1.451],[.113,.010,1.409],[.098,-.006,1.372],[.083,-.022,1.350]],.012,.0036),
('sideback-R',[[.066,.021,1.497],[.084,.040,1.501],[.101,.061,1.471],[.106,.072,1.431],[.098,.064,1.391],[.081,.047,1.360],[.068,.031,1.344]],.012,.0034),
('lowerfront-L',[[-.067,-.055,1.484],[-.087,-.056,1.485],[-.105,-.050,1.462],[-.112,-.047,1.429],[-.105,-.053,1.392],[-.092,-.065,1.365]],.009,.0025),
('lowerside-L',[[-.071,-.006,1.457],[-.091,.007,1.465],[-.108,.017,1.443],[-.115,.017,1.410],[-.103,.005,1.375],[-.089,-.011,1.350]],.010,.0028),
('lowerfront-R',[[.067,-.050,1.485],[.088,-.049,1.485],[.106,-.039,1.458],[.112,-.034,1.423],[.102,-.042,1.387],[.088,-.056,1.361]],.009,.0026),
('lowerside-R',[[.070,.001,1.454],[.090,.015,1.460],[.107,.029,1.434],[.110,.028,1.401],[.096,.013,1.369],[.081,-.003,1.347]],.010,.0029),
('occiput-L2',[[-.046,.043,1.509],[-.060,.067,1.513],[-.073,.088,1.485],[-.079,.105,1.449],[-.071,.110,1.409],[-.058,.094,1.372],[-.045,.078,1.346]],.012,.0035),
('occiput-L1',[[-.023,.049,1.515],[-.031,.075,1.518],[-.043,.098,1.485],[-.049,.113,1.445],[-.040,.114,1.404],[-.029,.097,1.369],[-.020,.082,1.345]],.012,.0034),
('occiput-C',[[0,.050,1.513],[.001,.078,1.514],[.005,.101,1.481],[.009,.116,1.440],[.004,.115,1.398],[-.003,.099,1.366],[-.007,.082,1.343]],.012,.0035),
('occiput-R1',[[.023,.048,1.511],[.033,.076,1.515],[.047,.099,1.481],[.052,.115,1.439],[.043,.114,1.399],[.031,.096,1.365],[.023,.079,1.342]],.012,.0034),
('occiput-R2',[[.046,.040,1.505],[.060,.068,1.510],[.076,.091,1.477],[.079,.107,1.438],[.068,.110,1.399],[.054,.093,1.364],[.041,.076,1.341]],.012,.0035),
('nape-L',[[-.037,.039,1.446],[-.046,.067,1.451],[-.057,.087,1.429],[-.058,.102,1.397],[-.047,.096,1.368],[-.036,.082,1.344]],.010,.0027),
('nape-C',[[0,.039,1.437],[-.002,.067,1.443],[-.003,.091,1.420],[.001,.105,1.389],[-.002,.096,1.361],[-.007,.081,1.340]],.011,.003),
('nape-R',[[.037,.038,1.443],[.046,.066,1.448],[.057,.089,1.423],[.054,.103,1.391],[.042,.095,1.362],[.031,.078,1.341]],.010,.0028)]
def sample(P,n=65):
 P=np.array(P,float);Q=np.vstack((P[0],P,P[-1]));out=[]
 for i in range(len(P)-1):
  p0,p1,p2,p3=Q[i:i+4]
  for t in np.linspace(0,1,12,endpoint=False):out.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t**3))
 out=np.vstack((out,P[-1]));arc=np.r_[0,np.linalg.norm(np.diff(out,axis=0),axis=1).cumsum()];return np.stack([np.interp(np.linspace(0,arc[-1],n),arc,out[:,j]) for j in range(3)],1)
def main():
 tick=time.time();t=json.loads((E/'before.json').read_text());assert not OUT.exists() and a.a.sha(Path(t['source']))==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];old=bpy.data.objects[a.FIXED[1]];old.material_slots[0].link='DATA';bpy.data.objects[a.FIXED[2]].hide_render=False;bpy.data.objects[a.FIXED[2]].hide_set(False);bpy.data.objects['AFN184_ACTUAL_NATIVE_DEFORMED_LASHES'].hide_render=True;bpy.data.objects['AFN184_ACTUAL_NATIVE_DEFORMED_LASHES'].hide_set(True);protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};W,T=a.geometry(skin);sf=np.load(E.parent/'r0171-actual-scalp-chart/actual-scalp-groom-lineage.npz')['actualScalpFaces'];tree=BVHTree.FromPolygons(W.tolist(),T[sf].tolist(),all_triangles=True);verts=[];faces=[];paths=[];records=[];railTri=[];railBC=[];railWorld=[]
 def anchor(seed):
  hit,no,fi,gap=tree.find_nearest(Vector(seed));f=int(sf[fi]);B=W[T[f]];uv=np.linalg.lstsq(np.column_stack((B[1]-B[0],B[2]-B[0])),np.array(hit)-B[0],rcond=None)[0];bc=np.clip(np.array([1-uv.sum(),*uv]),0,1);bc/=bc.sum();normal=unit(np.cross(B[1]-B[0],B[2]-B[0]));return bc@B,normal,T[f],bc,float(gap)
 for cid,(name,keys,width,depth) in enumerate(STROKES):
  root,normal,tr,bc,gap=anchor(keys[0]);growth=unit(np.array(keys[1])-root);P=[root+normal*.00004,root+normal*.0035+growth*.0025]+keys[1:];path=sample(P);paths.append(path);tangent=np.gradient(path,axis=0);tangent/=np.linalg.norm(tangent,axis=1,keepdims=True);cross=unit(np.cross(tangent[1],normal))
  if np.linalg.norm(cross)<.1:cross=np.array([1.,0.,0.])
  x=cross;start=len(verts);rootRails=[];along=np.linspace(0,1,65)
  for k,p in enumerate(path):
   x=unit(x-tangent[k]*float(x@tangent[k]));y=unit(np.cross(tangent[k],x));w=width*np.interp(along[k],[0,.06,.20,.45,.73,.91,1],[.45,.65,1,1.05,.95,.60,.035]);d=depth*np.interp(along[k],[0,.06,.25,.70,.92,1],[0,.65,1,.95,.45,.015])
   # A broad four-sided ridged bundle section, not detached ellipse tubes.
   section=[(-1,0),(-.5,.80),(0,1),(.5,.80),(1,0),(.5,-.45),(0,-.60),(-.5,-.45)]
   for j,(xx,yy) in enumerate(section):
    q=p+x*w*xx+y*d*yy
    if k==0:
     qr,nr,tt,bb,gg=anchor(root+x*w*xx);q=qr+nr*.00004;railTri.append(tt);railBC.append(bb);railWorld.append(q);rootRails.append(q.tolist())
    verts.append(q)
  for k in range(64):
   for j in range(8):faces.append([start+k*8+j,start+k*8+(j+1)%8,start+(k+1)*8+(j+1)%8,start+(k+1)*8+j])
  faces.append([start+j for j in reversed(range(8))]);faces.append([start+64*8+j for j in range(8)]);records.append({'id':cid,'region':name,'seedToActualSkinRootDistanceM':gap,'actualRoot':root.tolist(),'actualSkinTriangleVertices':tr.tolist(),'actualRootBC':bc.tolist(),'allEightActualRootBandRails':rootRails,'authoredWholeKeys':[list(p) for p in keys],'widthHalfM':width,'depthM':depth})
 mesh=bpy.data.meshes.new('AFN188_CURRENT_ROOT_BANDS_PRIMARY_VOLUME_DATA');mesh.from_pydata(np.array(verts).tolist(),[],faces);mesh.update();hair=bpy.data.objects.new('AFN188_ACTUAL_CURRENT_PRIMARY_CLUMP_VOLUMES',mesh);s.collection.objects.link(hair)
 for p in mesh.polygons:p.use_smooth=True
 mat=bpy.data.materials.new('AFN188_COARSE_FORM_BROWN_NOT_FINAL_FIBRE_MATERIAL');mat.use_nodes=True;ns=mat.node_tree.nodes;ns.clear();bs=ns.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(.055,.022,.011,1);bs.inputs['Roughness'].default_value=.6;output=ns.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs[0],output.inputs[0]);mesh.materials.append(mat);gd=bpy.data.hair_curves.new('AFN188_CURRENT_COMPLETE_PRIMARY_GUIDES_DATA');gd.add_curves([65]*len(paths));gd.position_data.foreach_set('vector',np.array(paths,'f4').ravel());gd.attributes.new('AFN188_GUIDE_ID','INT','CURVE').data.foreach_set('value',np.arange(len(paths),dtype='i4'));go=bpy.data.objects.new('AFN188_EDITABLE_CURRENT_PRIMARY_GUIDES',gd);s.collection.objects.link(go);go.hide_render=True;go.hide_set(True);old.hide_render=True;old.hide_set(True);s.camera.data.type='PERSP';bpy.context.view_layer.update();assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected}
 np.savez_compressed(E/'current-primary-clump-lineage.npz',paths=np.array(paths,'f4'),rootRailTriangles=np.array(railTri,'i4'),rootRailBC=np.array(railBC),actualRootRailWorld=np.array(railWorld),meshWorld=np.array(verts,'f4'));save('direct-current-primary-authoring.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':'COARSE_PRIMARY_FORM_NOT_COMPLETE_HAIR','primaryClumps':len(paths),'actualRootBandRails':len(railTri),'actualPrimaryConstruction':records,'changedFailedPremise':'Each complete clump authored on current head, eight root-band rails anchored on actual current Skin; full widths/depths/ear/occiput/nape strokes differ by region. Unlike178 detached point-root elliptical tubes, current root bands are actual Skin-owned and clumps have ridged broad sections. No foreign guide/cache transfer, distance-style field, source-card UV or failed free-tail preservation. Coarse full form must be viewed before children.','noNewHairFibresOrMotionYet':True,'originalSevenRawMeshUVSignaturesRetained':True,'fullFiniteSelfContinuousContactUnaccepted':True,'secondsBeforePreview':time.time()-tick})
 hair['scope']='Coarse primary form stage only. Current Skin-owned root bands and authored complete clump volumes; not realistic fibres, natural motion, complete appearance/function/contact/runtime adoption.';a.b.u.v.E=E;views=[a.b.u.v.image('coarse-current-primary-clumps','face')];bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);save('coarse-build-summary.json',{'source':t['source'],'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'engineAlias':str(R/'engine/assets/characters/female-next/source/r0188-source'/OUT.name),'actualSkin':skin.name,'actualRig':'AFN138_ACTUAL_CURRENT_GAZE_RIG','actualHair':hair.name,'actualGuides':go.name,'retainedSourceHair':old.name,'primaryClumps':len(paths),'rootBandRails':len(railTri),'completeWomanScenes':1,'fullFineHairCandidate':False,'coarseFormOnly':True,'unaccepted':True,'secondsBeforeOtherViews':time.time()-tick})
 for v in ['body-face','profile','back','oblique']:views.append(a.b.u.v.image('coarse-current-primary-clumps',v));save('coarse-current-preview-controls.json',views)
 print('R188_CURRENT_ROOT_BANDS_COARSE_COMPLETE_WOMAN_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
