"""Reconstructed original Blender car primitives/rig serializer. Not recovered V12 source.
No project-wide reuse license has been selected for original project material;
third-party components retain their stated licenses.
"""
import bpy,bmesh,math,struct,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
CURRENT=None

def reset():
 global CURRENT
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.unit_settings.system='METRIC';CURRENT=None

def material(name,c,metal=0,rough=.4,emit=0,alpha=1,coat=.2):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,alpha);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;p.inputs['Alpha'].default_value=alpha;p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.17
 if emit:p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=emit
 if alpha<1:m.surface_render_method='DITHERED';m.use_transparency_overlap=False
 return m

def empty(name,loc=(0,0,0),parent=None):
 o=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(o);o.parent=parent;o.location=loc;return o

def parent_keep(o,parent):
 bpy.context.view_layer.update();mw=o.matrix_world.copy();o.parent=parent;o.matrix_world=mw

def mesh(name,vs,fs,mat,smooth=True,bevel=0,normal_hint=None):
 me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);me.materials.append(mat);bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if normal_hint and sum((f.normal*f.calc_area()for f in bm.faces),Vector()).dot(Vector(normal_hint))<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
 bm.to_mesh(me);bm.free()
 for p in me.polygons:p.use_smooth=smooth
 if bevel:
  b=o.modifiers.new('Manufactured edge radii','BEVEL');b.width=bevel;b.segments=2;b.harden_normals=True;b=o.modifiers.new('Weighted edge normals','WEIGHTED_NORMAL');b.keep_sharp=True
 if CURRENT:parent_keep(o,CURRENT)
 return o

def box(name,loc,size,mat,bevel=.005):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if bevel:
  b=o.modifiers.new('Manufactured edge radii','BEVEL');b.width=bevel;b.segments=3;b.harden_normals=True;b=o.modifiers.new('Weighted edge normals','WEIGHTED_NORMAL');b.keep_sharp=True
 if CURRENT:parent_keep(o,CURRENT)
 return o

def cylinder(name,loc,r,depth,mat,axis='Z',n=32):
 rot=(0,math.pi/2,0)if axis=='X'else(math.pi/2,0,0)if axis=='Y'else(0,0,0);bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=depth,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 if CURRENT:parent_keep(o,CURRENT)
 return o

def torus(name,loc,major,minor,mat,axis='Y',n=40,m=8):
 rot=(0,math.pi/2,0)if axis=='X'else(math.pi/2,0,0)if axis=='Y'else(0,0,0);bpy.ops.mesh.primitive_torus_add(major_segments=n,minor_segments=m,major_radius=major,minor_radius=minor,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 if CURRENT:parent_keep(o,CURRENT)
 return o

def line(name,pts,r,mat,sides=6):
 pts=[Vector(p)for p in pts];vs=[];fs=[]
 for i,p in enumerate(pts):
  t=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized();a=t.cross(Vector((0,0,1)))
  if a.length<.01:a=t.cross(Vector((0,1,0)))
  a.normalize();b=t.cross(a).normalized()
  for j in range(sides):ang=2*math.pi*j/sides;vs.append(p+r*(a*math.cos(ang)+b*math.sin(ang)))
 for i in range(len(pts)-1):
  for j in range(sides):q=i*sides+j;fs.append((q,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,q+sides))
 fs.extend([tuple(reversed(range(sides))),tuple((len(pts)-1)*sides+j for j in range(sides))]);return mesh(name,vs,fs,mat,True)

def panel(name,fn,ni,nj,mat,normal_hint=(0,0,1)):
 vs=[fn(i/ni,j/nj)for i in range(ni+1)for j in range(nj+1)];fs=[]
 for i in range(ni):
  for j in range(nj):q=i*(nj+1)+j;fs.append((q,q+nj+1,q+nj+2,q+1))
 return mesh(name,vs,fs,mat,True,normal_hint=normal_hint)

def apply_mod(o,mod):bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
def cut(obj,cutter,name):
 mod=obj.modifiers.new(name,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;apply_mod(obj,mod);bpy.data.objects.remove(cutter,do_unlink=True)
def prism(name,outline,zmin,zmax,mat):
 N=len(outline);vs=[(x,y,z)for z in(zmin,zmax)for x,y in outline];fs=[tuple(reversed(range(N))),tuple(N+i for i in range(N))]+[(i,(i+1)%N,(i+1)%N+N,i+N)for i in range(N)];return mesh(name,vs,fs,mat,False)
def smooth_interp(rows,x):
 for i in range(len(rows)-1):
  a,b=rows[i],rows[i+1]
  if x<=b[0]:
   dt=b[0]-a[0];t=max(0,min(1,(x-a[0])/dt));prev=rows[max(0,i-1)];nxt=rows[min(len(rows)-1,i+2)];out=[]
   for k in range(1,len(a)):
    ma=(b[k]-prev[k])/(b[0]-prev[0]);mb=(nxt[k]-a[k])/(nxt[0]-a[0]);out.append((2*t**3-3*t*t+1)*a[k]+(t**3-2*t*t+t)*dt*ma+(-2*t**3+3*t*t)*b[k]+(t**3-t*t)*dt*mb)
   return tuple(out)
 return tuple(rows[-1][1:])

def export_glb(groups,path,manifest):
 """Serialize direct geometry children per rigid group, merging only by material.
 Zero-area faces skipped before serialization. Does not create derivative scene objects.
 """
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();C=Matrix(((1,0,0),(0,0,1),(0,-1,0)));g={'asset':{'version':'2.0','generator':'Reconstructed original Blender rigid-part serializer'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[],'meshes':[],'materials':[],'buffers':[{'byteLength':0}],'bufferViews':[],'accessors':[],'extensionsUsed':['KHR_materials_clearcoat','KHR_materials_emissive_strength']};binary=bytearray();mats={};worldcoords=[];counts={};degenerate=0
 def accessor(values,kind,ctype,target=None,bounds=False):
  while len(binary)%4:binary.append(0)
  start=len(binary);flat=[x for row in values for x in row]if kind!='SCALAR'else values;binary.extend(struct.pack('<'+str(len(flat))+('f'if ctype==5126 else'I'),*flat));view={'buffer':0,'byteOffset':start,'byteLength':len(binary)-start}
  if target:view['target']=target
  vi=len(g['bufferViews']);g['bufferViews'].append(view);a={'bufferView':vi,'componentType':ctype,'count':len(values),'type':kind}
  if bounds:a.update({'min':[min(v[i]for v in values)for i in range(3)],'max':[max(v[i]for v in values)for i in range(3)]})
  ai=len(g['accessors']);g['accessors'].append(a);return ai
 def mat_index(m):
  if m.name in mats:return mats[m.name]
  p=m.node_tree.nodes.get('Principled BSDF');c=list(p.inputs['Base Color'].default_value);c[3]=p.inputs['Alpha'].default_value;d={'name':m.name,'pbrMetallicRoughness':{'baseColorFactor':c,'metallicFactor':p.inputs['Metallic'].default_value,'roughnessFactor':p.inputs['Roughness'].default_value},'doubleSided':c[3]<1 or bool(m.get('double_sided',False)),'extensions':{'KHR_materials_clearcoat':{'clearcoatFactor':p.inputs['Coat Weight'].default_value,'clearcoatRoughnessFactor':p.inputs['Coat Roughness'].default_value}}}
  if c[3]<1:d['alphaMode']='BLEND'
  e=p.inputs['Emission Strength'].default_value
  if e:d['emissiveFactor']=list(p.inputs['Emission Color'].default_value)[:3];d['extensions']['KHR_materials_emissive_strength']={'emissiveStrength':e}
  mats[m.name]=len(g['materials']);g['materials'].append(d);return mats[m.name]
 for group in groups:
  node={'name':group.name};loc,rot,scale=group.matrix_local.decompose();node['translation']=list(C@loc);q=(C@rot.to_matrix()@C.transposed()).to_quaternion();node['rotation']=[q.x,q.y,q.z,q.w];node['scale']=[scale.x,scale.z,scale.y];children=[i for i,o in enumerate(groups)if o.parent==group]
  if children:node['children']=children
  per={};parts=[o for o in group.children if o.type in('MESH','FONT','CURVE')]
  for oi,obj in enumerate(parts):
   ev=obj.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();xf=group.matrix_world.inverted()@obj.matrix_world;nm=xf.to_3x3().inverted().transposed();worldcoords.extend(C@(obj.matrix_world@v.co)for v in me.vertices)
   for tri in me.loop_triangles:
    verts=[C@(xf@me.vertices[i].co)for i in tri.vertices]
    if(verts[1]-verts[0]).cross(verts[2]-verts[0]).length_squared<1e-18:degenerate+=1;continue
    mi=mat_index(me.materials[tri.material_index]);p=per.setdefault(mi,{'positions':[],'normals':[],'indices':[],'lookup':{}})
    for li in tri.loops:
     vi=me.loops[li].vertex_index;v=C@(xf@me.vertices[vi].co);n=(C@(nm@me.corner_normals[li].vector)).normalized();key=(oi,vi,round(n.x,6),round(n.y,6),round(n.z,6))
     if key not in p['lookup']:p['lookup'][key]=len(p['positions']);p['positions'].append(tuple(v));p['normals'].append(tuple(n))
     p['indices'].append(p['lookup'][key])
   ev.to_mesh_clear()
  primitives=[]
  for mi,p in per.items():primitives.append({'attributes':{'POSITION':accessor(p['positions'],'VEC3',5126,34962,True),'NORMAL':accessor(p['normals'],'VEC3',5126,34962)},'indices':accessor(p['indices'],'SCALAR',5125,34963),'material':mi,'mode':4})
  if primitives:node['mesh']=len(g['meshes']);g['meshes'].append({'name':group.name+'_Geometry','primitives':primitives})
  counts[group.name]={'source_parts':len(parts),'triangles':sum(len(p['indices'])//3 for p in per.values()),'draw_calls':len(primitives)};g['nodes'].append(node)
 g['buffers'][0]['byteLength']=len(binary);jb=json.dumps(g,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);binary+=b'\0'*((-len(binary))%4);blob=struct.pack('<III',0x46546c67,2,12+8+len(jb)+8+len(binary))+struct.pack('<II',len(jb),0x4E4F534A)+jb+struct.pack('<II',len(binary),0x004E4942)+binary;path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(blob)
 manifest.update({'file':path.name,'sha256':hashlib.sha256(blob).hexdigest(),'bytes':len(blob),'triangles':sum(v['triangles']for v in counts.values()),'draw_calls':sum(v['draw_calls']for v in counts.values()),'materials':len(g['materials']),'material_names':[m['name']for m in g['materials']],'rigid_groups':counts,'degenerate_triangles_removed':degenerate,'bounds_three_m':{'min':[min(v[i]for v in worldcoords)for i in range(3)],'max':[max(v[i]for v in worldcoords)for i in range(3)]}});return manifest

def build_wheels(root,groups,paint,alloy,rubber,prefix='Rebuilt',lateral=.924,spokes=5):
 global CURRENT
 steers={};wheels={};calipers={}
 for key in('Front_Left','Front_Right','Rear_Left','Rear_Right'):
  s=1 if key.endswith('Left')else-1;x=1.35 if key.startswith('Front')else-1.35;y=s*lateral;z=.368;st=empty('Steer_'+key,(x,y,z),root);sp=empty('Spin_'+key,parent=st);wg=empty('Wheel_'+key,parent=sp);cg=empty('Caliper_'+key,parent=st);steers[key]=st;wheels[key]=wg;calipers[key]=cg;groups.extend((st,sp,wg,cg));CURRENT=wg
  profile=[(-.128,.267),(-.137,.294),(-.132,.328),(-.113,.349),(-.080,.355),(.080,.355),(.113,.349),(.132,.328),(.137,.294),(.128,.267)];v=[];f=[];N=56
  for j in range(N):a=2*math.pi*j/N;v.extend((x+r*math.cos(a),y+yy,z+r*math.sin(a))for yy,r in profile)
  for j in range(N):
   for k in range(len(profile)-1):q=j*len(profile)+k;f.append((q,((j+1)%N)*len(profile)+k,((j+1)%N)*len(profile)+k+1,q+1))
  mesh(prefix+' tire contact casing '+key,v,f,rubber,True)
  for yy in(-.060,0,.060):torus('Fine molded tire groove '+key,(x,y+yy,z),.3537,.0014,rubber,'Y',56,4)
  torus('Forged outer machined wheel lip '+key,(x,y+s*.137,z),.274,.009,alloy,'Y',48,8);torus('Forged inner wheel barrel lip '+key,(x,y-s*.108,z),.268,.007,alloy,'Y',40,6)
  v=[(x+.267*math.cos(2*math.pi*j/48),y+yy,z+.267*math.sin(2*math.pi*j/48))for yy in(-.108,.130)for j in range(48)];f=[(j,(j+1)%48,(j+1)%48+48,j+48)for j in range(48)];mesh('Open alloy wheel barrel '+key,v,f,alloy,True)
  def strip(name,coords):
   v=[]
   for dep in(-.009,.009):
    for r,off,w,a in coords:
     d=Vector((math.cos(a),0,math.sin(a)));t=Vector((-math.sin(a),0,math.cos(a)));c=Vector((x,y+s*(.143+dep),z))+d*r+t*off;v.extend((c-t*w,c+t*w))
   n=len(coords)*2;f=[]
   for j in range(len(coords)-1):q=j*2;f.extend([(q,q+2,q+3,q+1),(q+n,q+1+n,q+3+n,q+2+n),(q,q+n,q+2+n,q+2),(q+1,q+3,q+3+n,q+1+n)])
   f.extend([(0,1,1+n,n),(n-2,2*n-2,2*n-1,n-1)]);mesh(name,v,f,alloy,False,.002)
  for j in range(spokes):
   a=2*math.pi*j/spokes;strip('Forged radial wheel stem '+key,[(.052,0,.020,a),(.145,.012,.018,a)])
   for sg in(-1,1):strip('Tapered split wheel spoke '+key,[(.14,.012,.014,a),(.205,sg*.028,.012,a),(.265,sg*.042,.009,a)])
  cylinder('Center lock wheel hub '+key,(x,y+s*.148,z),.064,.032,alloy,'Y',32);cylinder('Unbranded wheel center recess '+key,(x,y+s*.168,z),.034,.011,rubber,'Y',24)
  for j in range(spokes):
   a=2*math.pi*j/spokes;cylinder('Wheel locking bolt '+key,(x+.047*math.cos(a),y+s*.171,z+.047*math.sin(a)),.006,.009,alloy,'Y',8)
  rr=[.072,.125,.158,.174,.190,.206,.222];N=72;v=[(x+r*math.cos(2*math.pi*j/N),y+s*(.073+dep),z+r*math.sin(2*math.pi*j/N))for dep in(-.008,.008)for r in rr for j in range(N)];faces=[];valid={(k,j):not(k in(3,4)and j%6==k-3)for k in range(len(rr)-1)for j in range(N)};n=len(rr)*N
  for(k,j),yes in valid.items():
   if not yes:continue
   q=k*N+j;q2=k*N+(j+1)%N;quad=(q,q2,q2+N,q+N);faces.extend([quad,tuple(reversed(tuple(q+n for q in quad)))])
   for edge,neighbor in[((q,q2),(k-1,j)),((q2,q2+N),(k,(j+1)%N)),((q2+N,q+N),(k+1,j)),((q+N,q),(k,(j-1)%N))]:
    if not valid.get(neighbor,False):a,b=edge;faces.append((a,b,b+n,a+n))
  mesh('Actually slotted ventilated rotor '+key,v,faces,alloy,False);CURRENT=cg
  for off in(.046,.102):box('Fixed brake caliper cheek '+key,(x-.176,y+s*off,z+.043),(.105,.024,.180),paint,.022)
  box('Fixed brake caliper outer bridge '+key,(x-.236,y+s*.075,z+.01),(.018,.083,.10),paint,.009)
 bpy.context.view_layer.update()
 for key,st in steers.items():
  hub=st.matrix_world.translation.copy();ratio=.366/.355;radial=Matrix.Translation(hub)@Matrix.Diagonal((ratio,1,ratio,1))@Matrix.Translation(-hub)
  for group in(wheels[key],calipers[key]):
   for o in group.children:
    if o.type!='MESH':continue
    old=o.matrix_world.copy();new=old.copy();t=old.translation-hub;new.translation=hub+Vector((t.x*ratio,t.y,t.z*ratio));o.data.transform(new.inverted()@radial@old);o.matrix_world=new
 return {'steers':steers,'wheels':wheels,'calipers':calipers,'radius':.366}

def cockpit(paint,carbon,glass,alloy,interior,white):
 box('Low central cockpit floor',(-.25,0,.275),(1.85,1.18,.065),carbon,.022);box('Cockpit rear structural firewall',(-1.02,0,.56),(.035,1.16,.55),carbon,.012)
 for s in(-1,1):
  y=s*.325;v=[];f=[];rows=[(-.46,.36,.21),(-.57,.49,.235),(-.64,.69,.23),(-.75,.90,.24),(-.81,1.025,.15)]
  for x,z,w in rows:
   for u in(-1,-.6,0,.6,1):v.append((x+.095*abs(u)**2,y+w*u,z+.025*abs(u)))
  for i in range(4):
   for j in range(4):q=i*5+j;f.append((q,q+1,q+6,q+5))
  o=mesh('Moulded sport bucket shell',v,f,interior,True,normal_hint=(1,0,0));so=o.modifiers.new('Bucket real shell thickness','SOLIDIFY');so.thickness=.027;box('Contoured sport seat cushion',(-.35,y,.405),(.45,.35,.10),interior,.045)
  for sg in(-1,1):
   line('Deep sculpted seat bolster',[(-.13,y+sg*.175,.42),(-.45,y+sg*.20,.49),(-.62,y+sg*.21,.74),(-.73,y+sg*.21,.91)],.043,interior,9);line('Fine seat contrast piping',[(-.14,y+sg*.17,.46),(-.46,y+sg*.18,.52),(-.64,y+sg*.18,.77),(-.75,y+sg*.18,.94)],.0035,paint,5);box('Seat harness opening',(-.73,y+sg*.08,.916),(.018,.085,.036),carbon,.009)
  box('Harness center buckle',(-.25,y,.47),(.065,.063,.025),alloy,.008)
 box('Curved low dashboard',(.45,0,.725),(.38,1.14,.16),interior,.055);box('Floating central tunnel',(-.06,0,.37),(1.12,.19,.14),carbon,.035);box('Driver instrument binnacle',(.255,-.36,.84),(.14,.33,.14),carbon,.035);box('Dark digital instrument face',(.178,-.36,.853),(.008,.27,.085),glass,.012)
 for j in range(5):box('Instrument original shift-light marker',(.170,-.448+j*.044,.875),(.004,.020,.004),white,.001)
 for y in(-.48,.42):cylinder('Circular dashboard air outlet',(.245,y,.76),.046,.016,carbon,'X',24);torus('Air outlet machined rim',(.233,y,.76),.041,.003,alloy,'X',24,5)
 line('Steering column',[(.37,-.36,.72),(.16,-.36,.825)],.018,carbon,8);torus('Right hand steering rim',(.13,-.36,.84),.128,.016,interior,'X',40,8)
 for a in(0,2.1,4.2):line('Steering spoke skeleton',[(.13,-.36,.84),(.13,-.36+math.cos(a)*.111,.84+math.sin(a)*.111)],.010,alloy,6)
 cylinder('Unbranded steering center',(.12,-.36,.84),.033,.018,carbon,'X',24)
 for y in(-.46,-.35,-.24):box('Machined driver pedal',(.40,y,.34),(.045,.055,.075),alloy,.005)
 for x in(-.09,.04,.17):box('Original drive selector switch',(x,0,.45),(.055,.06,.020),alloy,.007)
