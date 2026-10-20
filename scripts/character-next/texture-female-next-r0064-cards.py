"""Own reproducible card albedo/coverage/normal/flow atlas and scalp material.

The atlas is a 2-D virtual-fibre approximation, NOT physical strand geometry.
All artwork/data is generated here; no reference photograph is copied.
"""
from pathlib import Path
import bpy,numpy as np,json,time,math,importlib.util
s=importlib.util.spec_from_file_location('card64texturebase',Path(__file__).with_name('build-female-next-r0064-guide-ribbons.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
E=m.E;S=m.S;SRC=S/'aevrynd-female-next-r0064-b-scalp-free-card-shape.blend';OUT=S/'aevrynd-female-next-r0064-c-textured-card-study.blend';TEX=S/'study-r0064-textures';TEX.mkdir(exist_ok=True)

def atlas():
    W,H=1024,1024;tiles=8;tw=W//tiles;rng=np.random.default_rng(64064);rgba=np.zeros((H,W,4),'f4');normal=np.full_like(rgba,.5);normal[:,:,2:]=1.;flow=np.full_like(normal,.5);flow[:,:,1]=1.;flow[:,:,3]=1.;v=np.linspace(0,1,H);rows=np.arange(H)
    for tile in range(tiles):
        for i in range(92):
            u=(i+.5)/92+rng.uniform(-.003,.003);phase=rng.uniform(0,math.tau);amp=rng.uniform(.003,.013);freq=rng.uniform(3,8);end=rng.uniform(.72,1.0);radius=rng.uniform(.55,1.10);x=(u+amp*np.sin(v*freq+phase)*v)*tw-.5
            active=v<end;taper=np.clip((end-v)/.06,0,1);strandcolor=np.array((.060,.023,.010))*rng.uniform(.55,1.25);dx=amp*(np.sin(v*freq+phase)+v*freq*np.cos(v*freq+phase));direction=np.stack((dx,np.ones(H),np.zeros(H)),axis=1);direction/=np.linalg.norm(direction,axis=1)[:,None]
            for offset in (-2,-1,0,1,2):
                col=np.floor(x).astype('i4')+offset;relative=(col-x)/radius;cov=np.clip(1-np.abs(relative),0,1)*taper*active;mask=(col>=0)&(col<tw)&(cov>0);rr=rows[mask];cc=col[mask]+tile*tw;old=rgba[rr,cc,3];take=cov[mask]>old;rr=rr[take];cc=cc[take];sel=np.flatnonzero(mask)[take];rgba[rr,cc,:3]=strandcolor[None]*(.72+.28*v[sel,None]);rgba[rr,cc,3]=cov[sel];nx=np.clip(relative[sel],-.96,.96);normal[rr,cc,:3]=np.stack((nx*.5+.5,np.full(len(nx),.5),np.sqrt(1-nx*nx)*.5+.5),axis=1);flow[rr,cc,:3]=direction[sel]*.5+.5
        # Root blending and soft card borders are part of the representation,
        # never a waiver of actual card/body/self contact tests.
        u=(np.arange(tw)+.5)/tw;edge=np.minimum(np.clip(u/.06,0,1),np.clip((1-u)/.06,0,1));rgba[:,tile*tw:(tile+1)*tw,3]*=edge[None]*np.clip(v/.045,0,1)[:,None]
    images=[]
    for name,data in [('hair-linear-albedo-coverage',rgba),('hair-tangent-normal',normal),('hair-uv-flow',flow)]:
        im=bpy.data.images.new('AFN64_'+name,W,H,alpha=True);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(data.ravel());im.file_format='PNG';im.filepath_raw=str(TEX/(name+'.png'));im.save();im.filepath='//study-r0064-textures/'+name+'.png';im.pack();images.append(im)
    return images

def mat_card(images):
    mat=bpy.data.materials.new('AFN64_OWN_CARD_ATLAS_ANISOTROPIC_APPROX');mat.use_nodes=True;t=mat.node_tree;t.nodes.clear();out=t.nodes.new('ShaderNodeOutputMaterial');mix=t.nodes.new('ShaderNodeMixShader');transparent=t.nodes.new('ShaderNodeBsdfTransparent');bs=t.nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=.47;bs.inputs['Anisotropic'].default_value=.65
    al=t.nodes.new('ShaderNodeTexImage');al.image=images[0];no=t.nodes.new('ShaderNodeTexImage');no.image=images[1];nm=t.nodes.new('ShaderNodeNormalMap');nm.uv_map='AFN64_CardUV';nm.inputs['Strength'].default_value=.45;t.links.new(no.outputs['Color'],nm.inputs['Color']);t.links.new(nm.outputs['Normal'],bs.inputs['Normal']);t.links.new(al.outputs['Color'],bs.inputs['Base Color']);t.links.new(al.outputs['Alpha'],mix.inputs[0]);t.links.new(transparent.outputs[0],mix.inputs[1]);t.links.new(bs.outputs[0],mix.inputs[2]);t.links.new(mix.outputs[0],out.inputs['Surface']);attr=t.nodes.new('ShaderNodeAttribute');attr.attribute_name='AFN64_HairTangent';t.links.new(attr.outputs['Vector'],bs.inputs['Tangent']);return mat

def cap_material(images):
    mat=bpy.data.materials.new('AFN64_SCALP_UNDERCOAT_DIRECTIONAL_APPROX');mat.use_nodes=True;t=mat.node_tree;t.nodes.clear();out=t.nodes.new('ShaderNodeOutputMaterial');bs=t.nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=.55;bs.inputs['Anisotropic'].default_value=.65
    tex=t.nodes.new('ShaderNodeTexImage');tex.image=images[0];uv=t.nodes.new('ShaderNodeUVMap');uv.uv_map='AFN64_ScalpUV';t.links.new(uv.outputs[0],tex.inputs['Vector']);t.links.new(tex.outputs['Color'],bs.inputs['Base Color']);mix=t.nodes.new('ShaderNodeMixShader');tr=t.nodes.new('ShaderNodeBsdfTransparent');coverage=t.nodes.new('ShaderNodeAttribute');coverage.attribute_name='AFN64_Coverage';t.links.new(coverage.outputs['Fac'],mix.inputs[0]);t.links.new(tr.outputs[0],mix.inputs[1]);t.links.new(bs.outputs[0],mix.inputs[2]);t.links.new(mix.outputs[0],out.inputs['Surface']);tan=t.nodes.new('ShaderNodeAttribute');tan.attribute_name='AFN64_HairTangent';t.links.new(tan.outputs['Vector'],bs.inputs['Tangent']);nm=t.nodes.new('ShaderNodeNormalMap');nm.uv_map='AFN64_ScalpUV';nm.inputs['Strength'].default_value=.30;nt=t.nodes.new('ShaderNodeTexImage');nt.image=images[1];t.links.new(uv.outputs[0],nt.inputs['Vector']);t.links.new(nt.outputs['Color'],nm.inputs['Color']);t.links.new(nm.outputs['Normal'],bs.inputs['Normal']);return mat

def main():
    tick=time.time();m.g.E=E;m.shade.g.E=E
    if '--views' in __import__('sys').argv:
        ref=json.loads((E/'c-build-summary.json').read_text());assert m.sha(OUT)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(OUT));m.shade.settings();m.save('c-additional-view-controls.json',m.shade.render('c-card',('oblique','opposite-oblique','alternate-oblique','body-face')));return
    assert not OUT.exists();ref=json.loads((E/'b-build-summary.json').read_text());assert m.sha(SRC)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(SRC));images=atlas();cardmat=mat_card(images);capmat=cap_material(images);cards=sorted([o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN64_') and o.name.endswith('_CARD')],key=lambda o:o.name)
    body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];levels=[]
    for md in body.modifiers:
        if md.type=='SUBSURF':levels.append((md,md.levels));md.levels=md.render_levels
    bpy.context.view_layer.update();row=m.g.k.mesh(body)
    for i,o in enumerate(cards):
        d=o.data;data=np.array([v.co[:] for v in d.vertices]);rootrows=json.loads(o['rootRowsJSON'])
        # A card is anchored to the OUTSIDE of the declared0.8mm undercoat,
        # not claimed as individual follicles embedded in living skin.
        for j,rec in enumerate(rootrows):
            tri=row['V'][row['T'][int(rec[0])]];n=m.unit(np.cross(tri[1]-tri[0],tri[2]-tri[0]));d.vertices[j].co=np.array(rec[2:])@tri+n*.0008
        data=np.array([v.co[:] for v in d.vertices]).reshape(-1,3,3);centres=data.mean(1);tan=np.gradient(centres,axis=0);tan/=np.maximum(np.linalg.norm(tan,axis=1),1e-12)[:,None];a=d.attributes.new('AFN64_HairTangent','FLOAT_VECTOR','POINT');a.data.foreach_set('vector',np.repeat(tan,3,axis=0).astype('f4').ravel())
        for uv in d.uv_layers['AFN64_CardUV'].data:uv.uv.x=(uv.uv.x+i%8)/8
        d.materials.clear();d.materials.append(cardmat);o['scope']='Actual textured0-thickness hair card. Virtual fibre atlas is an approximation; root/body/self/dynamic contacts and physical strands unaccepted.';d.update()
    cap=bpy.data.objects['AFN64_SCALP_UNDERCOAT'];d=cap.data;P=np.array([v.co[:] for v in d.vertices]);normal=np.array([v.normal[:] for v in d.vertices]);x,y,z=P.T;front=np.clip((-.030-y)/.085,0,1);line=1.417+.102*front-.32*np.abs(x)*front;edge=np.clip((z-line)/.004,0,1);part=np.exp(-((x+.016)/.0013)**2)*np.clip((z-1.528)/.014,0,1)*np.clip((.022-y)/.02,0,1);coverage=edge*(1-part);d.attributes.new('AFN64_Coverage','FLOAT','POINT').data.foreach_set('value',coverage.astype('f4'));side=np.sign(x+.016);target=np.column_stack((side*.8,np.full(len(x),.2),np.full(len(x),-.3)));tan=target-normal*np.einsum('ij,ij->i',target,normal)[:,None];tan/=np.maximum(np.linalg.norm(tan,axis=1),1e-12)[:,None];d.attributes.new('AFN64_HairTangent','FLOAT_VECTOR','POINT').data.foreach_set('vector',tan.astype('f4').ravel());d.materials.clear();d.materials.append(capmat)
    for md,level in levels:md.levels=level
    m.shade.settings();m.g.k.b.camera('face');bpy.context.scene['AFN64_status']='OWN_TEXTURED_CARD_HAIRSTYLE_TRIAL_NOT_PHYSICAL_STRANDS_OR_RUNTIME_ACCEPTANCE';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    m.save('c-build-summary.json',{'source':str(SRC),'sourceSha256':m.sha(SRC),'output':str(OUT),'outputSha256':m.sha(OUT),'cards':len(cards),'textures':[{'relative':im.filepath,'sha256':m.sha(Path(bpy.path.abspath(im.filepath))),'packed':bool(im.packed_file),'size':list(im.size),'colorSpace':im.colorspace_settings.name} for im in images],'atlasConstruction':'Own deterministic2-D virtual-fibre albedo/coverage, cylindrical tangent normal and UV flow. No photograph or external asset pixels used. Not3-D fibre collision evidence.','rootRepresentation':'Actual source triangle/barycentric plus outward0.8mm undercoat offset on card root row. Not individual physical follicles.','skinBodyEyesChanged':False,'guidesLive':False,'contacts':'UNTESTED','engine':'NOT_TESTED','secondsBeforePreview':time.time()-tick})
    m.save('c-first-view-controls.json',m.shade.render('c-card',('face','profile','back')))
if __name__=='__main__':main()
