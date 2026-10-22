"""Original reference-inspired scenic assets. No copied sculpture mesh/photo textures.
Blender meters +X forward +Y left +Z up; GLB +X forward +Y up -Z left.
The bird is a new stylized guardian interpretation, not a measured Jatayu replica.
"""
import bpy, math, random, json, hashlib, struct, os
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/landscape_reference_kit'; WEB=ROOT/'assets/web'
OUT.mkdir(parents=True,exist_ok=True);WEB.mkdir(parents=True,exist_ok=True)
random.seed(9197); CURRENT=None;M={}

def clear():
 global CURRENT
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);CURRENT=None
 bpy.context.scene.unit_settings.system='METRIC'
def mat(name,col,rough=.7,metal=0,group='Surface'):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;m['web_group']=group
 if group=='Stone':
  nt=m.node_tree;tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=15;tex.inputs['Detail'].default_value=3;bum=nt.nodes.new('ShaderNodeBump');bum.inputs['Strength'].default_value=.35;bum.inputs['Distance'].default_value=.065;nt.links.new(tex.outputs['Fac'],bum.inputs['Height']);nt.links.new(bum.outputs['Normal'],p.inputs['Normal']);p.inputs['Roughness'].default_value=.94;p.inputs['Specular IOR Level'].default_value=.22
 M[name]=m;return m
def empty(name):
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);return o
def mesh(name,vs,fs,m,smooth=False):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);me.materials.append(m);o.parent=CURRENT
 for p in me.polygons:p.use_smooth=smooth
 return o
def box(name,loc,size,m,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);o.parent=CURRENT
 if bevel:
  b=o.modifiers.new('Hand softened edge','BEVEL');b.width=bevel;b.segments=2
  b=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');b.keep_sharp=True
 return o
def ell(name,loc,size,m,segs=20,rings=12):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,radius=1,location=loc);o=bpy.context.object;o.name=name;o.scale=size;o.data.materials.append(m);o.parent=CURRENT
 for p in o.data.polygons:p.use_smooth=True
 return o
def path_tube(name,pts,radii,m,sides=8):
 vs=[];fs=[]
 for i,p in enumerate(pts):
  p=Vector(p);t=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(i-1,0)]);t.normalize();a=t.cross(Vector((0,0,1)))
  if a.length<.05:a=t.cross(Vector((0,1,0)))
  a.normalize();b=t.cross(a).normalized()
  for j in range(sides):
   ph=2*math.pi*j/sides;vs.append(p+radii[i]*(math.cos(ph)*a+math.sin(ph)*b))
 for i in range(len(pts)-1):
  for j in range(sides):q=i*sides+j;fs.append((q,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,q+sides))
 fs.extend([tuple(reversed(range(sides))),tuple((len(pts)-1)*sides+j for j in range(sides))]);return mesh(name,vs,fs,m,True)
def tube(name,a,b,r,m,sides=8):return path_tube(name,[a,b],[r,r],m,sides)
def feather(name,a,b,width,thick,m,arch=.5):
 a,b=Vector(a),Vector(b);direction=(b-a).normalized();side=direction.cross(Vector((0,0,1))).normalized();up=side.cross(direction).normalized();vs=[];fs=[]
 for i,t in enumerate((0,.15,.38,.63,.85,1)):
  center=a.lerp(b,t)+Vector((0,0,math.sin(t*math.pi)*arch));w=width*(.25+.75*math.sin(t*math.pi)**.6) if i<5 else .035
  for j in range(6):
   ph=2*math.pi*j/6;vs.append(center+side*(math.cos(ph)*w)+up*(math.sin(ph)*thick*(.3+.7*math.sin(t*math.pi))))
 for i in range(5):
  for j in range(6):q=i*6+j;fs.append((q,i*6+(j+1)%6,(i+1)*6+(j+1)%6,q+6))
 fs.extend([tuple(reversed(range(6))),tuple(30+j for j in range(6))]);return mesh(name,vs,fs,m,True)

def bird():
 global CURRENT
 clear();CURRENT=empty('BirdRockLookout')
 rocks=[mat('Guardian basalt '+str(i),c,.91,group='Rock') for i,c in enumerate([(.10,.105,.085),(.145,.13,.105),(.17,.15,.115),(.12,.135,.095),(.19,.16,.12)])]
 stones=[mat('Guardian warm carved stone '+str(i),c,.66,group='Stone') for i,c in enumerate([(.34,.205,.105),(.39,.25,.13),(.44,.29,.16),(.32,.215,.125),(.46,.315,.18)])]
 dark=mat('Guardian deep carved accents',(.12,.095,.063),.65,group='Accent')
 # Layered original rocky pedestal, lower foot exactly at ground root.
 vs=[];fs=[];N=80;levels=[(0,1),(.8,1.02),(2.8,.94),(5.0,.80),(7.3,.65),(8.7,.40),(9.2,.15)]
 for k,(z,r) in enumerate(levels):
  for j in range(N):
   a=2*math.pi*j/N;noise=1+.075*math.sin(5*a+.7*k)+.055*math.sin(11*a+1.3*k);vs.append((26*r*noise*math.cos(a),23*r*noise*math.sin(a),z+(.0 if k==0 else random.uniform(-.5,.5))))
 for k in range(len(levels)-1):
  for j in range(N):q=k*N+j;fs.append((q,k*N+(j+1)%N,(k+1)*N+(j+1)%N,q+N))
 fs.append(tuple((len(levels)-1)*N+j for j in range(N)));o=mesh('Rock hill layered strata',vs,fs,rocks[0],True)
 for m in rocks[1:]:o.data.materials.append(m)
 for p in o.data.polygons:p.material_index=1
 for i in range(21):
  a=i*2.399;r=random.uniform(.65,.94);x=26*r*math.cos(a);y=23*r*math.sin(a);z=next((za+(zb-za)*(r-ra)/(rb-ra) for (za,ra),(zb,rb) in zip(levels[1:],levels[2:]) if rb<=r<=ra),4.5)
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(x,y,z+.15));o=bpy.context.object;o.name='Weathered exposed rock outcrop '+str(i);o.scale=(random.uniform(1.7,3.4),random.uniform(1.4,2.8),random.uniform(.8,1.5));o.data.materials.append(rocks[i%5]);o.parent=CURRENT
  for v in o.data.vertices:v.co*=random.uniform(.87,1.12)
  for po in o.data.polygons:po.use_smooth=True
  dec=o.modifiers.new('Rock silhouette budget','DECIMATE');dec.ratio=.40
 # Bird's reclining central mass flows through the curved neck into uplifted head.
 ell('Reclining chest',(-1,0,10.8),(8.8,5.5,4.1),stones[0],28,16)
 ell('Lower resting mantle',(-7,0,9.5),(6.8,4.6,2.9),stones[1],24,12)
 neck=path_tube('Continuous swept neck',[(3.5,0,11),(7,0,11.8),(10,0,14),(12.5,0,16.5),(14.0,0,17.5)],[3.6,3.2,2.65,2.15,1.9],stones[1],16)
 ell('Watchful head',(14.4,0,17.7),(2.65,2.0,2.4),stones[2],24,14)
 # Hooked raptor beak, broad nasal bridge and downward hooked tip.
 path_tube('Hooked raptor beak',[(16.1,0,17.85),(18.5,0,17.3),(19.4,0,16.45),(19.1,0,15.6)],[1.25,.95,.55,.035],stones[4],8)
 for s in (-1,1):
  ell('Inset vigilant eye',(15.2,s*1.77,18.15),(.45,.16,.31),dark,16,8)
  path_tube('Carved fierce brow',[(14.2,s*1.65,18.65),(15.0,s*1.97,18.63),(15.8,s*1.63,18.45)],[.23,.25,.13],stones[3],8)
  # Swept upper-wing mantle, then separate tapering feathers in overlapping fans.
  ell('Wing shoulder '+str(s),(-1,s*4.5,11.4),(5.7,3.0,2.2),stones[1],20,12)
  for i in range(12):
   a=(-1+i*.25,s*(3.4+i*.08),11.8-i*.10);b=(-15+i*1.55,s*(11.3+6.8*math.sin((i+1)/14*math.pi)),7.6+.1*i)
   feather('Outer layered primary '+str(s)+' '+str(i),a,b,1.00,.28,stones[i%5],.9)
  for i in range(11):
   a=(1.1-i*.55,s*3.4,12.6);b=(-9.5+i*1.20,s*(10.7+1.4*math.sin(i*.35)),10.0+.17*i)
   feather('Middle covert '+str(s)+' '+str(i),a,b,.82,.32,stones[(i+2)%5],.8)
  for i in range(9):
   a=(3.6-i*.87,s*2.7,13.6-.12*i);b=(1.1-i*.95,s*6.2,12.3-.10*i)
   feather('Upper shoulder scale '+str(s)+' '+str(i),a,b,.63,.26,stones[(i+1)%5],.3)
  for i in range(6):
   feather('Neck layered scale '+str(s)+' '+str(i),(7.5+i*.8,s*1.6,12.6+i*.63),(5.5+i*.85,s*2.35,11.8+i*.64),.65,.17,stones[(i+2)%5],.3)
 # Overlapping carved neck plumes conform to the side of the curved neck.
 for sign in (-1,1):
  for row in range(6):
   for col in range(2):
    x=7.1+row*1.08;z=12.4+row*.73+col*.65
    points=[]
    for xx,zz in ((x,z),(x-1.35,z-.60)):
     hit,pt,no,idx=neck.ray_cast(Vector((xx,sign*20,zz)),Vector((0,-sign,0)))
     if hit:points.append(pt+no*.17)
    if len(points)==2:feather('Projected layered neck plume '+str(sign)+str(row)+str(col),points[0],points[1],.42,.10,stones[(row+col)%5],.04)
 # Overlapping breast and mantle scales remove a blank geometric torso.
 for row in range(7):
  x=4.2-row*1.7
  for col in range(7):
   y=(col-3)*1.12+(.32 if row%2 else 0)
   def surface(xx,yy):return 10.8+4.1*math.sqrt(max(.045,1-((xx+1)/8.8)**2-(yy/5.5)**2))
   a=(x,y,surface(x,y)+.16);bx=x-2.8;by=y*1.10;b=(bx,by,surface(bx,by)+.17)
   feather('Overlapping carved breast plume '+str(row)+' '+str(col),a,b,.67,.15,stones[(row+col)%5],.10)
 # Fine sculpted quill ridges emphasize the scale of the long wing primaries.
 for sign in (-1,1):
  for i in range(12):
   a=Vector((-1+i*.25,sign*(3.4+i*.08),11.8-i*.10));b=Vector((-15+i*1.55,sign*(11.3+6.8*math.sin((i+1)/14*math.pi)),7.6+.1*i))
   ps=[a.lerp(b,t)+Vector((0,0,math.sin(t*math.pi)*.9+.23)) for t in (.2,.45,.7,.88)]
   path_tube('Carved primary central ridge '+str(sign)+' '+str(i),ps,[.07,.08,.055,.015],stones[3],5)
 # Long tapered tail feathers fall naturally onto the rocky base.
 for i in range(11):
  t=(i-5)/5;feather('Long tail fan '+str(i),(-6,t*2,10.5),(-20.2+abs(t)*1.8,t*8.2,5.5+abs(t)*.8),1.0,.24,stones[(i+1)%5],1.0)
 # Raised curled talons, composed as readable but restrained sculptural details.
 for s in (-1,1):
  path_tube('Folded leg '+str(s),[(0,s*3.1,11.8),(2,s*4.1,14.5),(4.3,s*3.8,14.0)],[.88,.76,.53],stones[3],10)
  for i in range(3):
   y=s*(3.1+i*.7);path_tube('Curled talon '+str(s)+' '+str(i),[(4.0,y,14),(5.4,y,14.1),(5.8,y,13.5),(5.2,y,13.1)],[.3,.27,.18,.035],stones[2],8)
 return CURRENT,{'reference':'7A8EA1B8: broad reclining bird, layered wings and rock summit; original stylized sculpture, not exact replica.','collision_proxies':[{'type':'obb','center_local_m':[.385,4.85,-.497],'half_extents_m':[28.822,4.85,24.089],'part':'conservative rocky pedestal envelope'},{'type':'obb','center_local_m':[-1,11.2,0],'half_extents_m':[9.0,4.2,5.8],'part':'solid central bird body'},{'type':'capsule','a_local_m':[4,11.8,0],'b_local_m':[14.4,17.7,0],'radius_m':2.7,'part':'upright neck and head'},{'type':'capsule','a_local_m':[16.1,17.85,0],'b_local_m':[19.1,15.6,0],'radius_m':1.25,'part':'hooked beak'}],'solid_note':'Conservative solid rock/body/head proxies; outer thin feather tips are scenic. Keep viewpoint traffic outside rocky footprint.'}

def shikara():
 global CURRENT
 clear();CURRENT=empty('CanalShikara')
 wood=[mat('Shikara honey teak '+str(i),c,.48,group='Wood') for i,c in enumerate([(.30,.13,.047),(.46,.24,.08),(.55,.32,.115),(.37,.18,.055)])]
 dark=mat('Shikara dark hull',(.025,.055,.055),.38,group='Hull');blue=mat('Shikara muted azure canopy trim',(.025,.23,.30),.58,group='Textile');cane=mat('Shikara woven cane',(.58,.43,.22),.84,group='Textile');cloth=mat('Shikara warm seat fabric',(.72,.58,.34),.86,group='Textile');steel=mat('Shikara brass fittings',(.52,.33,.09),.33,.65,group='Wood')
 # Fine displacement hull shell; slender upswept bow and transom, open inside.
 xs=[-4.05,-3.65,-2.8,-1.4,0,1.4,2.8,3.65,4.2];ws=[.12,.48,.91,1.12,1.16,1.07,.77,.35,.025];zs=[.48,.28,.22,.22,.22,.24,.35,.61,.95]
 vs=[];fs=[]
 for x,w,z in zip(xs,ws,zs):
  vs.extend([(x,-w,z),(x,-w*.78,-.29),(x,0,-.53),(x,w*.78,-.29),(x,w,z)])
 for i in range(len(xs)-1):
  for j in range(4):q=i*5+j;fs.append((q,q+1,q+6,q+5))
 o=mesh('Open slender timber hull',vs,fs,dark,True);sol=o.modifiers.new('Planked hull thickness','SOLIDIFY');sol.thickness=.065
 for s in (-1,1):
  path_tube('Continuous upswept gunwale '+str(s),[(x,s*w,z+.025) for x,w,z in zip(xs,ws,zs)],[.07]*len(xs),wood[2],8)
  path_tube('Hull waterline trim '+str(s),[(x,s*w*.84,-.16+.5*z) for x,w,z in zip(xs,ws,zs)],[.027]*len(xs),wood[1],6)
 for i in range(14):
  x=-2.65+i*.4;width=1.8 if abs(x)<1.8 else 1.4
  box('Individual teak deck plank '+str(i),(x,0,.02),(.385,width,.075),wood[i%4],.012)
 for x in (-3.2,3.1):box('Raised bow and stern cross seat',(x,0,.41),(.45,1.24,.13),wood[2],.045)
 # Open seating: six low seats, split aisle, no closed passenger box.
 for x in (-1.6,-.3,1.0):
  for s in (-1,1):
   box('Low seat timber base',(x,s*.52,.31),(.72,.68,.42),wood[1],.055)
   box('Woven seat cushion',(x,s*.52,.55),(.69,.65,.12),cloth,.07)
   box('Seat sloped back',(x-.31,s*.52,.82),(.12,.65,.48),wood[2],.035).rotation_euler.y=-.12
   for y in (-.22,.22):tube('Seat cane upright',(x-.37,s*.52+y,.68),(x-.34,s*.52+y,1.04),.024,cane)
 # High curved woven canopy, bamboo ribs and fabric border.
 NX=11;NY=12;vs=[];fs=[]
 for i in range(NX):
  x=-2.62+i*5.02/(NX-1)
  for j in range(NY):
   y=-1.13+j*2.26/(NY-1);z=2.06+.42*(1-(y/1.13)**2)+.06*math.cos(x*.8);vs.append((x,y,z))
 for i in range(NX-1):
  for j in range(NY-1):q=i*NY+j;fs.append((q,q+1,q+NY+1,q+NY))
 mesh('Curved woven palm canopy',vs,fs,cane,True)
 for x in (-2.55,-1.25,.05,1.35,2.35):
  ps=[(x,-1.13+j*2.26/12,2.04+.42*(1-((-1.13+j*2.26/12)/1.13)**2)+.06*math.cos(x*.8)) for j in range(13)]
  path_tube('Visible bent bamboo canopy rib',ps,[.031]*13,wood[1],6)
 for s in (-1,1):
  path_tube('Azure canopy rolled edge '+str(s),[(-2.66,s*1.13,2.02),(-1.5,s*1.13,2.08),(0,s*1.13,2.12),(1.5,s*1.13,2.08),(2.44,s*1.13,2.01)],[.075]*5,blue,8)
  for x in (-2.45,0,2.25):
   tube('Canopy slender post',(x,s*.98,.24),(x,s*1.06,2.11),.036,wood[1]);tube('Canopy corner diagonal',(x,s*1.04,1.73),(x+.29,s*1.11,2.15),.023,wood[2])
  for x in (-2.55,2.35):tube('Open side railing upright',(x,s*.98,.24),(x,s*.98,.83),.025,wood[2])
  tube('Low open passenger handrail',(-2.55,s*.98,.83),(2.35,s*.98,.83),.035,wood[2])
 # Canopy texture is actual narrow geometric longitudinal binding, no bitmap.
 for j in range(19):
  y=-1.08+j*.12;z=2.07+.42*(1-(y/1.13)**2);path_tube('Canopy woven longitudinal binding',[(-2.6,y,z),(0,y,z+.06),(2.4,y,z)],[.009]*3,wood[2] if j%3==0 else cane,4)
 # Long oar on starboard and a small outboard at the stern.
 tube('Stowed wooden pole',(-3.2,-1.23,.45),(2.0,-1.23,.54),.035,wood[2]);feather('Carved oar blade',(2,-1.23,.54),(2.85,-1.23,.56),.16,.035,wood[1],0)
 box('Small outboard motor cowling',(-3.7,0,.62),(.42,.38,.44),dark,.11);tube('Outboard submerged leg',(-3.8,0,.42),(-3.8,0,-.63),.055,dark)
 for x in (-3.2,3.1):
  for s in (-1,1):ell('Woven rope mooring fender',(x,s*.54,.23),(.12,.13,.26),cane,10,6)
 return CURRENT,{'reference':'2D597ABA: small narrow open boats under curved pale woven canopies, original scenic shikara interpretation.','collision_proxies':[{'type':'obb','center_local_m':[.075,.98,0],'half_extents_m':[4.225,1.62,1.27],'part':'hull and canopy'}],'pivot':'waterline Y=0','wake_socket_local_m':[-4.05,0,0],'motion':'Rigid scenic root; no articulated riders or marine dynamics.'}

def tree():
 global CURRENT
 clear();CURRENT=empty('CanalRainTree');rng=random.Random(712)
 bark=[mat('Rain tree bark '+str(i),c,.96,group='Bark') for i,c in enumerate([(.12,.13,.07),(.20,.18,.10),(.25,.24,.13),(.16,.18,.085)])]
 leaf=[mat('Rain tree leaf '+str(i),c,.88,group='Leaf') for i,c in enumerate([(.025,.095,.012),(.055,.15,.018),(.085,.19,.026),(.12,.245,.042),(.035,.125,.016),(.16,.255,.05)])]
 # Strong asymmetrical trunk and arching lateral boughs, with flared buttress roots.
 trunk=[(0,0,0),(.15,0,1.2),(.65,.1,3.1),(1.4,.05,5.2),(2.8,.2,7.0),(4.2,.3,8.5),(5.8,.35,9.1)]
 path_tube('Gnarled leaning primary trunk',trunk,[.92,.84,.72,.65,.56,.43,.19],bark[0],12)
 for i in range(8):
  a=i*math.pi/4;path_tube('Flared root buttress '+str(i),[(math.cos(a)*2.1,math.sin(a)*1.6,.04),(math.cos(a)*.9,math.sin(a)*.7,.35),(.2,0,1.4)],[.07,.29,.42],bark[i%4],7)
 endpoints=[]
 branches=[((1.7,0,5.8),(-4.7,-3.5,8.3),(-9,-4.8,9.7)),((1.8,0,5.8),(-3,5,9.1),(-7.8,7.8,10.8)),((2.8,.2,7.0),(4.4,-5.0,9.6),(7.3,-9.0,10.8)),((3.5,.1,7.8),(8.4,3.2,9.5),(12.5,5.4,10.5)),((5.4,.3,8.9),(9.1,-2.4,10.5),(13,-3.8,11.4)),((1.9,.1,6),(0,-5.5,8.5),(-2.8,-10.1,9.9)),((2.0,.4,6.2),(3.1,6.5,9.2),(5.1,10.6,10.4))]
 for bi,(a,b,c) in enumerate(branches):
  a,b,c=Vector(a),Vector(b),Vector(c);mid=a.lerp(b,.5)+Vector((0,0,.3));path_tube('Heavy arching bough '+str(bi),[a,mid,b,c],[.48,.38,.24,.055],bark[bi%4],9)
  for j,t in enumerate((.3,.55,.78,1.0)):
   p=b.lerp(c,t);d=(c-b).normalized();side=Vector((-d.y,d.x,0));sign=1 if j%2 else-1;tip=p+side*(1.5+1.3*t)*sign+Vector((-.3,.2,1.6));path_tube('Tapered crown branch '+str(bi)+' '+str(j),[b,p,tip],[.15,.11,.025],bark[(bi+1)%4],6);endpoints.append(tip)
  endpoints.append(c+Vector((0,0,.5)))
 endpoints.extend([Vector((3,0,11)),Vector((0,0,10.5)),Vector((6,0,11.3))])
 # Multi-lobed flattened umbrella foliage, fine geometric pointed leaves around uneven edges.
 for ci,center in enumerate(endpoints):
  # Low-poly dark internal foliage volume hides view-through holes without alpha textures.
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=center);o=bpy.context.object;o.name='Irregular fine crown mass '+str(ci);o.scale=(rng.uniform(1.7,2.45)*.64,rng.uniform(1.5,2.2)*.64,rng.uniform(.65,1.0)*.64);o.parent=CURRENT
  for m in leaf:o.data.materials.append(m)
  for v in o.data.vertices:v.co*=rng.uniform(.82,1.18)
  for p in o.data.polygons:p.material_index=ci%3;p.use_smooth=True
  # Sprays radiate well beyond each core: actual folded blades rather than square alpha planes.
  vs=[];fs=[]
  for k in range(135):
   ang=rng.random()*2*math.pi;rr=math.sqrt(rng.random());top=1 if rng.random()<.57 else -1
   p=center+Vector((math.cos(ang)*rr*2.45,math.sin(ang)*rr*2.15,top*math.sqrt(max(0,1-rr*rr))*rng.uniform(.7,1.14)))
   length=rng.uniform(.32,.57);width=length*.44;direction=Vector((math.cos(ang+rng.uniform(-.6,.6)),math.sin(ang),rng.uniform(-.28,.35))).normalized();side=Vector((-direction.y,direction.x,0)).normalized();base=len(vs)
   vs.extend([p-direction*length,p+side*width+Vector((0,0,.035)),p+direction*length,p-side*width+Vector((0,0,.035))]);fs.extend([(base,base+1,base+2),(base,base+2,base+3)])
  o=mesh('Pointed compound leaf sprays '+str(ci),vs,fs,leaf[ci%6],True)
  for m in leaf:o.data.materials.append(m)
  for k in range(135):
   color=rng.randrange(6)
   for q in (k*2,k*2+1):o.data.polygons[q].material_index=color
 # Fine raised bark fissures follow the taper, not flat painted texture.
 for i in range(13):
  a=i*2*math.pi/13;ps=[]
  for j,p in enumerate(trunk):
   r=[.92,.84,.72,.65,.56,.43,.19][j];ps.append(Vector(p)+Vector((math.cos(a+j*.07)*r,math.sin(a+j*.07)*r,0)))
  path_tube('Raised twisting bark rib '+str(i),ps,[.035,.045,.04,.035,.03,.025,.008],bark[(i+1)%4],4)
 # Thin hanging twigs soften the arch, not collision objects.
 for i in range(16):
  p=endpoints[i*2%len(endpoints)];path_tube('Hanging fine twig '+str(i),[p,p+Vector((.15,.1,-.8)),p+Vector((.3,.2,-1.4))],[.025,.014,.002],bark[i%4],4)
 return CURRENT,{'reference':'2D597ABA: dense spreading rain-tree-like broadleaf canopy and low arching gnarled limbs, not coconut palms.','collision_proxies':[{'type':'capsule','a_local_m':[0,0,0],'b_local_m':[1.4,5.2,-.05],'radius_m':.96,'part':'lower primary trunk'},{'type':'capsule','a_local_m':[1.4,5.2,-.05],'b_local_m':[5.8,9.1,-.35],'radius_m':.65,'part':'upper primary trunk'},{'type':'obb','center_local_m':[0,.22,0],'half_extents_m':[2.2,.35,1.8],'part':'flared root buttresses'}],'foliage_collision':False,'leaf_material':'RainTree_Leaf','wind_contract':'Existing /leaf|frond|grass/i material match; material vertex heights are root-local, crown starts ~8m. Strength .07m is suitable. No whole-trunk sway.','placement_note':'Set trunk at canal bank, rotate +X arch toward water; broad crown overlaps opposite tree visually, not road collider.'}

BUILDERS={'BirdRockLookout':bird,'CanalShikara':shikara,'CanalRainTree':tree}

def original_stone_normal():
 # Periodic multi-scale stochastic stone micro-relief; entirely original, no photo input.
 N=256;rng=np.random.default_rng(92714);noise=rng.normal(size=(N,N));fy=np.fft.fftfreq(N)[:,None];fx=np.fft.fftfreq(N)[None,:];freq=np.sqrt(fx*fx+fy*fy)
 filt=np.exp(-(freq/.19)**2)/(1+(freq/.035)**2);height=np.fft.ifft2(np.fft.fft2(noise)*filt).real;height=height/(height.std()+1e-8)*.007
 dx=(np.roll(height,-1,axis=1)-np.roll(height,1,axis=1))*N/(2*1.25);dy=(np.roll(height,-1,axis=0)-np.roll(height,1,axis=0))*N/(2*1.25)
 normals=np.stack((-dx,-dy,np.ones_like(dx)),axis=-1);normals/=np.linalg.norm(normals,axis=-1)[...,None];rgba=np.ones((N,N,4),dtype=np.float32);rgba[:,:,:3]=normals*.5+.5
 im=bpy.data.images.new('Original procedural stone microrelief',width=N,height=N,alpha=False);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(rgba.reshape(-1));im.filepath_raw=str(OUT/'original_stone_normal.png');im.file_format='PNG';im.save();im.pack();return im

def bake(src,key):
 dg=bpy.context.evaluated_depsgraph_get();vs=[];fs=[];cs=[];gs=[];ns=[];smooth=[];groups=[]
 for o in list(src.children_recursive):
  if o.type!='MESH':continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();xf=src.matrix_world.inverted()@o.matrix_world;nm=xf.to_3x3().inverted().transposed();base=len(vs);vs.extend([xf@v.co for v in me.vertices])
  for p in me.polygons:
   m=me.materials[p.material_index];group=m['web_group']
   if group not in groups:groups.append(group)
   gs.append(groups.index(group));fs.append(tuple(base+i for i in p.vertices));cs.append(tuple(m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value));smooth.append(p.use_smooth)
   for li in p.loop_indices:ns.append((nm@me.corner_normals[li].vector).normalized())
  ev.to_mesh_clear()
 mats=[]
 for group in groups:
  name=('RainTree_'+group) if key=='CanalRainTree' else(key+'_'+group);m=mat(name,(1,1,1),.94 if group in ('Rock','Stone') else .84 if group in ('Leaf','Bark','Textile') else .6)
  nt=m.node_tree;p=nt.nodes.get('Principled BSDF');attr=nt.nodes.new('ShaderNodeVertexColor');attr.layer_name='AssetColor';nt.links.new(attr.outputs['Color'],p.inputs['Base Color']);p.inputs['Specular IOR Level'].default_value=.22 if group in ('Rock','Stone') else .5;m.use_backface_culling=False
  if key=='BirdRockLookout' and group=='Stone':
   tex=nt.nodes.new('ShaderNodeTexImage');tex.image=original_stone_normal();tex.interpolation='Linear';tex.extension='REPEAT';normal=nt.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.72;nt.links.new(tex.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],p.inputs['Normal'])
  mats.append(m)
 nr=empty(key+'_WEB');me=bpy.data.meshes.new(key+'_Optimized');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(key+'_Geometry',me);bpy.context.collection.objects.link(o);o.parent=nr
 for m in mats:me.materials.append(m)
 attr=me.color_attributes.new(name='AssetColor',type='FLOAT_COLOR',domain='CORNER')
 for p,gi,c,sm in zip(me.polygons,gs,cs,smooth):
  p.material_index=gi;p.use_smooth=sm
  for li in p.loop_indices:
   cc=c
   if key=='BirdRockLookout' and groups[gi] in ('Rock','Stone'):
    v=me.vertices[me.loops[li].vertex_index].co
    broad=math.sin(v.x*.76+math.sin(v.y*.83))*math.sin(v.y*.92+v.z*.65)
    fine=math.sin(v.x*5.2+v.y*2.3)*math.sin(v.z*5.4-v.y*3.5)
    variation=.84+.15*broad+.055*fine
    cc=(c[0]*variation,c[1]*variation,c[2]*variation,1)
   attr.data[li].color=cc
 me.normals_split_custom_set(ns)
 if key=='BirdRockLookout':
  uv=me.uv_layers.new(name='StoneMicroUV')
  for p in me.polygons:
   normal=p.normal;axis=max(range(3),key=lambda i:abs(normal[i]))
   for li in p.loop_indices:
    v=me.vertices[me.loops[li].vertex_index].co
    uv.data[li].uv=((v.y if axis==0 else v.x)*.8,(v.y if axis==2 else v.z)*.8)
 return nr,mats

def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def light(loc,energy,size,color):
 d=bpy.data.lights.new('Preview softbox','AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new('Preview softbox',d);bpy.context.collection.objects.link(o);o.location=loc;aim(o,(0,0,4))
def preview(key):
 clear();bpy.ops.import_scene.gltf(filepath=str(WEB/(key+'.glb')));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=int(os.environ.get('KIT_SAMPLES','48'));sc.cycles.use_denoising=False;sc.render.resolution_x=1440;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
 w=bpy.data.worlds.new('Landscape soft atmosphere');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.29,.38,.44,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.55;sc.world=w
 f=mat('Preview neutral ground',(.12,.17,.13) if key!='CanalShikara' else(.065,.14,.13),.56 if key!='CanalShikara' else .22,.12 if key=='CanalShikara' else 0);bpy.ops.mesh.primitive_plane_add(size=500,location=(0,0,-.04));bpy.context.object.data.materials.append(f)
 if key=='BirdRockLookout':loc=(53,-65,51);target=(0,0,8);scale=64;size=30;power=35000
 elif key=='CanalRainTree':loc=(27,-33,20);target=(2,0,6);scale=33;size=18;power=12000
 else:loc=(9,-12,7);target=(0,0,.7);scale=10.9;size=8;power=1900
 light((size*.4,-size,size*1.6),power,size,(1,.88,.68));light((-size,size,size),power*.65,size,(.72,.84,1))
 d=bpy.data.cameras.new('Part presentation camera');d.type='ORTHO';d.ortho_scale=scale;cam=bpy.data.objects.new('Part presentation camera',d);bpy.context.collection.objects.link(cam);cam.location=loc;aim(cam,target);sc.camera=cam;sc.render.filepath=str(OUT/(key+'_preview.png'))
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(key+'_preview.blend')))
 if not os.environ.get('KIT_SKIP_RENDER'):bpy.ops.render.render(write_still=True)

keys=[os.environ['KIT_ONLY']] if os.environ.get('KIT_ONLY') else list(BUILDERS)
for key in keys:
 src,meta=BUILDERS[key]();bpy.context.view_layer.update();bpy.context.scene['source_note']='Original procedural geometry inspired by user reference pixels. No logos, textures or copied mesh.';bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(key+'.blend')))
 nr,mats=bake(src,key);bpy.context.view_layer.update();src.name=key+'_SOURCE';nr.name=key;bpy.ops.object.select_all(action='DESELECT');nr.select_set(True)
 for o in nr.children_recursive:o.select_set(True)
 path=WEB/(key+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_yup=True)
 blob=path.read_bytes();n=struct.unpack_from('<I',blob,12)[0];g=json.loads(blob[20:20+n]);tri=sum(g['accessors'][p['indices']]['count']//3 for me in g['meshes'] for p in me['primitives']);draws=sum(len(me['primitives']) for me in g['meshes']);coords=[v.co for o in nr.children_recursive if o.type=='MESH' for v in o.data.vertices];mn=[min(v[i] for v in coords) for i in range(3)];mx=[max(v[i] for v in coords) for i in range(3)]
 meta.update({'asset':key,'file':'assets/web/'+key+'.glb','root':key,'source':'assets/landscape_reference_kit/'+key+'.blend','generator':'blender/build_landscape_reference_kit.py','coordinates':'meters: Blender +X forward +Y left +Z up; GLB +X forward +Y up -Z left','root_pivot':'ground Y=0' if key!='CanalShikara' else 'waterline Y=0','bounds_local_m':{'min':[mn[0],mn[2],-mx[1]],'max':[mx[0],mx[2],-mn[1]]},'dimensions_xyz_m':[mx[0]-mn[0],mx[2]-mn[2],mx[1]-mn[1]],'triangles':tri,'draw_calls':draws,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest(),'materials':[m.name for m in mats],'images':len(g.get('images',[])),'license_note':'Original geometry and palette authored for this project; reference photograph not embedded or redistributed. Stylized interpretation, not measured replica.'})
 if key=='BirdRockLookout':
  meta['procedural_normal']={'image':'original_stone_normal.png','resolution':[256,256],'origin':'Original periodic multiscale stochastic micro-relief generated with fixed NumPy seed92714; no photograph input','embedded_in_glb':True}
  rp=[]
  for ob in nr.children_recursive:
   if ob.type!='MESH':continue
   for po in ob.data.polygons:
    if ob.data.materials[po.material_index].name.endswith('_Rock'):rp.extend([ob.data.vertices[i].co for i in po.vertices])
  lo=[min(v[i] for v in rp) for i in range(3)];hi=[max(v[i] for v in rp) for i in range(3)]
  meta['collision_proxies'][0]={'type':'obb','center_local_m':[(lo[0]+hi[0])/2,(lo[2]+hi[2])/2,-(lo[1]+hi[1])/2],'half_extents_m':[(hi[0]-lo[0])/2,(hi[2]-lo[2])/2,(hi[1]-lo[1])/2],'part':'conservative rocky pedestal envelope; computed from exported rock vertices'}
 if key=='CanalShikara':meta['collision_proxies']=[{'type':'obb','center_local_m':[(mn[0]+mx[0])/2,(mn[2]+mx[2])/2,-(mn[1]+mx[1])/2],'half_extents_m':[(mx[0]-mn[0])/2,(mx[2]-mn[2])/2,(mx[1]-mn[1])/2],'part':'conservative whole boat including canopy and stowed oar'}]
 (OUT/(key+'_manifest.json')).write_text(json.dumps(meta,indent=2));print('LANDSCAPE_EXPORTED',json.dumps(meta));preview(key)
manifest={'version':1,'assets':[json.loads(p.read_text()) for p in sorted(OUT.glob('*_manifest.json'))],'source_references':['reference-image-not-distributed','reference-image-not-distributed'],'reference_note':'User pixels inspected directly. Photographs are visual study only and excluded from shipped assets.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));(WEB/'landscape_reference_manifest.json').write_text(json.dumps(manifest,indent=2));print('LANDSCAPE_KIT_READY')
