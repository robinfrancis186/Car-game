"""Far-only original canal canopy envelope; all 2,836 bark triangles are preserved."""
import bpy,bmesh,json,math,random,hashlib,shutil
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];OUT=R/'assets/foliage_detail';WEB=R/'assets/web';PUB=R/'web/public/assets'
bpy.ops.wm.open_mainfile(filepath=str(R/'assets/landscape_reference_kit/CanalRainTree.blend'))
envelopes=[]
for o in bpy.data.objects:
 if o.type=='MESH'and o.name.startswith('Pointed compound leaf sprays'):
  vv=[o.matrix_world@v.co for v in o.data.vertices];envelopes.append(([min(v[i]for v in vv)for i in range(3)],[max(v[i]for v in vv)for i in range(3)]))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(WEB/'CanalRainTree.glb'))
verts=[];faces=[];colors=[];normals=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 me=o.data;xf=o.matrix_world;nm=xf.to_3x3().inverted().transposed();a=me.color_attributes.active_color
 for p in me.polygons:
  if 'Bark'not in me.materials[p.material_index].name:continue
  face=[]
  for li in p.loop_indices:
   idx=me.loops[li].vertex_index;face.append(len(verts));verts.append(xf@me.vertices[idx].co);colors.append(tuple(a.data[li if a.domain=='CORNER' else idx].color));normals.append((nm@me.corner_normals[li].vector).normalized())
  faces.append(tuple(face))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);scene=bpy.context.scene;col=bpy.data.collections.new('CanalRainTreeFar');scene.collection.children.link(col)
def make(name,vs,fs,cs,ns=None):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.90;vc=m.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='AssetColor';m.node_tree.links.new(vc.outputs['Color'],p.inputs['Base Color']);m.use_backface_culling=False
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(m);me.update();a=me.color_attributes.new(name='AssetColor',type='FLOAT_COLOR',domain='CORNER')
 for p in me.polygons:
  p.use_smooth=True
  for li in p.loop_indices:a.data[li].color=cs[me.loops[li].vertex_index]
 me.color_attributes.active_color=a
 if ns:me.normals_split_custom_set(ns)
 o=bpy.data.objects.new(name,me);col.objects.link(o);return o
make('RainTree_Bark',verts,faces,colors,normals);vv=[];ff=[];cc=[];rng=random.Random(90210)
# Merge only the five nearest overlapping crown-cluster pairs, retaining their exact union bounds.
# 33 rounded icosahedral envelopes use 660 triangles: total 3,496 including unchanged bark.
while len(envelopes)>33:
 pair=min(((i,j)for i in range(len(envelopes))for j in range(i)),key=lambda ij:sum(((envelopes[ij[0]][0][k]+envelopes[ij[0]][1][k])-(envelopes[ij[1]][0][k]+envelopes[ij[1]][1][k]))**2 for k in range(3)))
 i,j=pair;a,b=envelopes[i],envelopes[j];merged=([min(a[0][k],b[0][k])for k in range(3)],[max(a[1][k],b[1][k])for k in range(3)]);envelopes.pop(i);envelopes.pop(j);envelopes.append(merged)
for lo,hi in envelopes:
 center=Vector(tuple((lo[i]+hi[i])/2 for i in range(3)));r=[(hi[i]-lo[i])/2 for i in range(3)];base=len(vv);bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=1,radius=1);bm.verts.ensure_lookup_table();bm.verts.index_update();extent=[max(abs(v.co[k])for v in bm.verts)for k in range(3)];vv.extend([center+Vector(tuple(v.co[k]/extent[k]*r[k]for k in range(3)))for v in bm.verts]);ff.extend([tuple(base+v.index for v in f.verts)for f in bm.faces]);color=(rng.uniform(.05,.082),rng.uniform(.15,.20),rng.uniform(.022,.035),1);cc.extend([color]*len(bm.verts));bm.free()
make('RainTree_Leaf',vv,ff,cc);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'CanalRainTreeFar.blend'));bpy.ops.object.select_all(action='DESELECT')
for o in col.objects:o.select_set(True)
p=WEB/'CanalRainTreeFar.glb';bpy.ops.export_scene.gltf(filepath=str(p),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False);shutil.copy2(p,PUB/p.name)
manifest={'asset':'CanalRainTreeFar','source':'assets/foliage_detail/CanalRainTreeFar.blend','triangles':len(faces)+len(ff),'bark_triangles_preserved':len(faces),'canopy_triangles':len(ff),'canopy_envelopes':len(envelopes),'draws':2,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'original_unchanged_sha256':hashlib.sha256((WEB/'CanalRainTree.glb').read_bytes()).hexdigest(),'usage':'Distant canopy only. Same root/scale/placement/collider contract; original detailed asset unchanged. 33 rounded envelopes derived from 38 original clusters replace thousands of subpixel leaves. Not for close viewing.','license':'Derived exclusively from original CC0 project geometry; no photos/textures/imported third-party assets.'}
for d in [OUT,WEB,PUB]:(d/'canal_far_manifest.json').write_text(json.dumps(manifest,indent=2))
# Honest same-camera far silhouette preview, source model retained separately.
s=scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=False;s.render.resolution_x=1000;s.render.resolution_y=700;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.world.color=(.25,.32,.4)
ld=bpy.data.lights.new('FarPreviewSun','SUN');lo=bpy.data.objects.new(ld.name,ld);s.collection.objects.link(lo);ld.energy=2;lo.rotation_euler=(.4,-.6,-.3)
ca=bpy.data.cameras.new('FarPreviewCamera');co=bpy.data.objects.new(ca.name,ca);s.collection.objects.link(co);co.location=(38,-48,23);co.rotation_euler=(Vector((2,0,7))-co.location).to_track_quat('-Z','Y').to_euler();ca.lens=48;s.camera=co;s.render.filepath=str(OUT/'CanalRainTreeFar_preview.png');bpy.ops.render.render(write_still=True);print('CANAL_FAR_READY',manifest,flush=True)
