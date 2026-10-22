"""Original scenic transit kit. Reference-inspired, not operator CAD.
Blender +X forward +Y left +Z up, meters. GLB +X forward +Y up.
No photo textures, external mesh, official logos or rideable interiors.
"""
import bpy, math, json, hashlib, struct, os
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/infrastructure/vehicles'; WEB=ROOT/'assets/web'
OUT.mkdir(parents=True,exist_ok=True); WEB.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC'
M={}; CURRENT=None

def mat(key,col,metal=0,rough=.35,group='surface',emit=0):
 m=bpy.data.materials.new(key);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 p.inputs['Emission Color'].default_value=(*col,1);p.inputs['Emission Strength'].default_value=emit;m['web_group']=group;M[key]=m;return m
white=mat('Transit pearl white',(.74,.79,.8),.25,.29)
silver=mat('Metro brushed silver',(.42,.49,.52),.6,.32)
teal=mat('Coast turquoise',(.015,.61,.58),.24,.28)
blue=mat('Water transit ocean blue',(.018,.20,.42),.22,.32)
cyan=mat('Water transit cyan',(.035,.49,.64),.15,.34)
purple=mat('Water transit plum stripe',(.24,.06,.39),.16,.35)
glass=mat('Transit dark panoramic glass',(.012,.033,.042),.36,.15,'glazing')
black=mat('Transit charcoal equipment',(.021,.028,.034),.3,.45)
steel=mat('Transit satin stainless',(.29,.34,.36),.7,.29)
rubber=mat('Transit rubber fenders and bellows',(.008,.012,.014),.0,.6)
light=mat('Transit warm lamps',(.85,.95,1),.0,.2,'lamps',1.6)
red=mat('Transit red navigation',(.9,.01,.008),.0,.22,'lamps',1.7)
green=mat('Transit green navigation',(.01,.78,.16),.0,.22,'lamps',1.7)
amber=mat('Transit amber route display',(.9,.43,.035),.0,.2,'lamps',1.6)


def empty(name,loc=(0,0,0),parent=None):
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.location=loc;o.parent=parent;return o

def mesh(name,verts,faces,m,smooth=False):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(m)
 for p in me.polygons:p.use_smooth=smooth
 if CURRENT:o.parent=CURRENT
 return o

def box(name,loc,size,m,bevel=0,seg=2):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if CURRENT:o.parent=CURRENT
 if bevel:
  mod=o.modifiers.new('Soft manufactured edges','BEVEL');mod.width=bevel;mod.segments=min(seg,1) if CURRENT and CURRENT.name.startswith('TrainCar_') else seg
  mod=o.modifiers.new('Weighted face normals','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=40
 return o

def cyl(name,loc,r,depth,m,axis='Z',segments=16):
 bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(m)
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 if CURRENT:o.parent=CURRENT
 return o

def tube(name,a,b,r,m,segments=8):
 a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,m,segments=segments);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def panel(name,verts,m):
 return mesh(name,verts,[tuple(range(len(verts)))],m)

def side_rect(name,cx,y,cz,w,h,r,m,sign=1):
 # Rounded plane on lateral surface. Geometry only, no texture opacity sorting.
 pts=[]
 for dx,dz,a0 in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for i in range(4):
   a=math.radians(a0+i*30);pts.append((cx+dx+r*math.cos(a),y,cz+dz+r*math.sin(a)))
 if sign>0:pts.reverse()
 return panel(name,pts,m)

def text_obj(name,text,loc,size,m,side=1):
 cu=bpy.data.curves.new(name,'FONT');cu.body=text;cu.align_x='CENTER';cu.align_y='CENTER';cu.size=size;cu.extrude=0;cu.resolution_u=2
 o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(math.pi/2 if side<0 else math.pi/2,0,0 if side<0 else math.pi)
 cu.materials.append(m)
 if CURRENT:o.parent=CURRENT
 return o

def rounded_profile(w,zlo,zhi,r=.2):
 pts=[]
 for yc,zc,a0 in [(w/2-r,zhi-r,0),(-w/2+r,zhi-r,90),(-w/2+r,zlo+r,180),(w/2-r,zlo+r,270)]:
  for i in range(4):
   a=math.radians(a0+i*30);pts.append((yc+r*math.cos(a),zc+r*math.sin(a)))
 return pts

def loft(name,sections,m,cab=False):
 # x,width,low,high,corner-radius
 verts=[]
 for k,(x,w,lo,hi,r) in enumerate(sections):
  f=(1 if k==len(sections)-1 else .5 if k==len(sections)-2 else 0) if cab else 0
  verts.extend([(x-.48*max(0,z-1.5)*f,y,z) for y,z in rounded_profile(w,lo,hi,r)])
 n=16;faces=[tuple(reversed(range(n)))]
 for k in range(len(sections)-1):
  for j in range(n):faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
 faces.append(tuple((len(sections)-1)*n+j for j in range(n)))
 o=mesh(name,verts,faces,m,True);o.data.polygons[0].use_smooth=False;o.data.polygons[-1].use_smooth=False
 if cab:
  o.data.materials.append(teal)
  for p in o.data.polygons:
   if sum(o.data.vertices[i].co.x for i in p.vertices)/len(p.vertices)>7.3:p.material_index=1
 return o

def project(body,axis,a,z,side=1):
 origin=Vector((40,a,z)) if axis=='X' else Vector((a,40*side,z))
 direction=Vector((-1,0,0)) if axis=='X' else Vector((0,-side,0))
 ok,hit,normal,idx=body.ray_cast(origin,direction)
 if not ok:raise RuntimeError(f'Glazing projection missed {body.name} {axis} {a} {z}')
 return hit+normal*.018

def projected_glass(name,body,axis,ar,zr,m,side=1,cols=8,rows=6):
 vs=[];fs=[]
 for j in range(rows+1):
  t=j/rows;z=zr[0]+(zr[1]-zr[0])*t;edge=.065 if j in (0,rows) else 0
  for i in range(cols+1):
   u=i/cols;a=ar[0]+edge+(ar[1]-ar[0]-edge*2)*u;vs.append(project(body,axis,a,z,side))
 for j in range(rows):
  for i in range(cols):
   q=j*(cols+1)+i;face=(q,q+1,q+cols+2,q+cols+1);fs.append(face if (axis=='X' or side<0) else tuple(reversed(face)))
 return mesh(name,vs,fs,m,True)

train=empty('CoastMetroTrain');cars=[]
for ci,offset in enumerate((19.4,0,-19.4)):
 CURRENT=empty('TrainCar_'+str(ci),(offset,0,0),train);cars.append(CURRENT)
 # Build third car facing -X via parent rotation, preserving individual centered pivot.
 if ci==2:CURRENT.rotation_euler.z=math.pi
 if ci in (0,2):
  cabbody=loft('Metro_CabBody_'+str(ci),[(-9.3,2.78,.92,3.85,.28),(-9.05,2.9,.88,3.9,.32),(6.8,2.9,.88,3.9,.32),(7.5,2.88,.9,3.88,.35),(8.25,2.73,.96,3.78,.43),(8.85,2.45,1.04,3.55,.5),(9.3,2.45,1.14,3.48,.5)],silver,True)
  projected_glass('Metro panoramic front '+str(ci),cabbody,'X',(-1.07,1.07),(1.68,3.28),glass,cols=10,rows=8)
  a=project(cabbody,'X',0,1.78);b=project(cabbody,'X',.63,2.73);tube('Metro front wiper '+str(ci),a,b,.016,black)
  for side in (-1,1):
   projected_glass('Metro LED lens '+str(ci)+str(side),cabbody,'X',sorted((side*.72,side*1.02)),(1.38,1.52),light,cols=4,rows=2)
   side_rect('Metro cab side glass',7.65,side*1.438,2.75,1.05,1.35,.2,glass,side)
  box('Metro anticlimber',(9.32,0,1.09),(.22,1.63,.17),black,.04)
 else:loft('Metro center body',[(-9.3,2.78,.92,3.85,.28),(-9.05,2.9,.88,3.9,.32),(9.05,2.9,.88,3.9,.32),(9.3,2.78,.92,3.85,.28)],silver)
 box('Metro roof shadow',(-1.3 if ci in (0,2) else 0,0,3.895),(15.6 if ci in (0,2) else 17.9,2.24,.12),black,.1)
 box('Metro underslung equipment',(0,0,.83),(15.9,2.2,.43),black,.08)
 for side in (-1,1):
  side_rect('Metro turquoise waist',-.6,side*1.454,1.19,16.7,.19,.045,teal,side)
  side_rect('Metro navy pinstripe',-.6,side*1.456,1.035,16.7,.055,.02,blue,side)
  # Four double-leaf doors per side; three intervening panorama windows.
  for di,dx in enumerate((-6.25,-2.05,2.15,6.35)):
   if ci in (0,2) and dx>6:dx=5.9
   side_rect('Metro door rubber frame',dx,side*1.46,2.28,1.34,2.15,.1,black,side)
   side_rect('Metro flush double door',dx,side*1.465,2.28,1.23,2.03,.08,silver,side)
   for d in (-1,1):side_rect('Metro door vision panel',dx+d*.31,side*1.471,2.66,.47,1.08,.07,glass,side)
   box('Metro door seam',(dx,side*1.477,2.26),(.018,.008,1.91),black)
   side_rect('Metro door warning sill',dx,side*1.48,1.32,1.14,.045,.01,amber,side)
  for dx in (-4.15,.05,4.15):side_rect('Metro panoramic side window',dx,side*1.458,2.73,2.32,1.24,.16,glass,side)
  text_obj('Metro original name','COAST METRO',(-3.85,side*1.474,1.66),.22,blue,side)
 # Roof HVAC and fine slotted inlet pattern; no advertising textures.
 for x in (-4.5,4.1):
  box('Metro HVAC rounded case',(x,0,4.06),(3.1,1.75,.27),white,.13)
  for j in range(9):box('Metro HVAC louvers',(x-1.14+j*.285,0,4.205),(.10,1.34,.018),black)
 for bx in (-5.5,5.5):
  box('Metro bogie frame',(bx,0,.49),(2.3,1.9,.37),steel,.09)
  for ax in (-.75,.75):
   cyl('Metro wheel axle',(bx+ax,0,.39),.10,2.2,steel,'Y',12)
   for side in (-1,1):
    cyl('Metro forged wheel',(bx+ax,side*.7175,.39),.39,.16,black,'Y',20)
    cyl('Metro wheel metal rim',(bx+ax,side*.8075,.39),.31,.025,steel,'Y',20)
  for side in (-1,1):
   for x in (-.65,.65):box('Metro suspension housing',(bx+x,side*.83,.73),(.46,.4,.34),black,.06)
 # End-mounted corrugated flexible collars. Two halves nearly meet across .8m gap.
 ends=(-1,) if ci in (0,2) else (-1,1)
 for end in ends:
  box('Metro gangway dark core',(end*9.43,0,2.25),(.30,2.36,2.5),rubber,.10)
  for n in range(3):
   xx=end*(9.32+n*.13)
   for side in (-1,1):box('Metro accordion side rib',(xx,side*1.19,2.25),(.045,.075,2.45),black,.018,1)
   for z in (1.03,3.47):box('Metro accordion horizontal rib',(xx,0,z),(.045,2.4,.075),black,.018,1)
  box('Metro coupler',(end*9.5,0,.67),(.7,.3,.18),steel,.03)
CURRENT=None

# Ferry revision 2: user-supplied side and bow reference silhouette.
ferry=empty('WaterTransitFerry');CURRENT=ferry
pink=mat('Ferry magenta diagonal bridge pillar',(.65,.045,.28),.16,.3)
orange=mat('Ferry safety lifebuoy orange',(.98,.19,.015),.04,.4)
mint=mat('Ferry pale cyan wave',(.18,.69,.74),.14,.34)
hullpurple=mat('Ferry purple twin hull',(.24,.075,.36),.24,.32)
# Two visibly distinct square-ended pontoons. Nothing fills the water-level bow gap.
for side in (-1,1):
 box('Ferry purple catamaran pontoon',(0,side*3.08,-.10),(23.5,2.04,2.04),hullpurple,.12,2)
 box('Ferry black antifoul waterline',(0,side*3.08,-.91),(23.44,2.055,.30),black,.09,2)
 box('Ferry longitudinal hull rubbing strake',(-.1,side*4.11,.54),(22.9,.055,.10),purple,.025)
box('Ferry bridging deck',(0,0,.955),(23.7,8.2,.19),hullpurple,.055)
box('Ferry non-slip deck',(0,0,1.065),(23.35,7.95,.055),steel,.025)
# Lower, mostly white saloon behind a separately raised pilot house.
ferrybody=loft('Ferry long white saloon',[(-8.7,6.75,1.04,4.12,.18),(-8.5,6.9,1.04,4.15,.18),(4.55,6.9,1.04,4.15,.18)],white)
for side in (-1,1):
 # One continuous dark band, including the stepped low aft edge seen in the reference.
 outline=[(-5.45,3.65),(-5.38,3.83),(-5.22,3.91),(3.68,3.91),(3.89,3.81),(3.98,3.62),(3.98,1.98),(3.88,1.81),(3.68,1.74),(-2.7,1.74),(-2.95,1.66),(-3.18,1.35),(-3.38,1.27),(-5.16,1.27),(-5.36,1.40),(-5.45,1.60)]
 pts=[(x,side*3.464,z) for x,z in outline];panel('Ferry long saloon panoramic glass',pts if side<0 else list(reversed(pts)),glass)
 # Boarding doorway, rounded blue awning and rear machinery louvres.
 side_rect('Ferry passenger door frame',-6.25,side*3.47,2.31,1.25,2.47,.12,blue,side)
 side_rect('Ferry passenger door dark opening',-6.25,side*3.48,2.28,1.0,2.25,.08,glass,side)
 box('Ferry door center seal',(-6.25,side*3.491,2.2),(.025,.015,2.08),steel)
 box('Ferry passenger door blue awning',(-6.25,side*3.61,3.62),(1.58,.47,.14),blue,.09,3)
 for j in range(6):box('Ferry aft equipment louvers',(-7.72,side*3.465,2.45+j*.11),(.83,.014,.036),steel)
 # Short stern blue coaming behind open rear deck rails.
 box('Ferry stern blue side coaming',(-10.1,side*3.46,1.43),(3.05,.10,.72),blue,.04)
 # Original layered wave ribbons; actual colored mesh, no copied graphics or texture.
 for band,(ma,shift,thick) in enumerate(((mint,.26,.28),(cyan,.08,.24),(blue,-.07,.20))):
  vs=[];fs=[];n=70
  for i in range(n+1):
   x=-11.45+15.65*i/n;zc=1.28+.28*math.sin((x+9.5)*.66)+.12*math.sin((x+8)*1.08)+shift
   vs.extend([(x,side*(3.473+band*.003),zc-thick/2),(x,side*(3.473+band*.003),zc+thick/2)])
  for i in range(n):
   f=(2*i,2*i+2,2*i+3,2*i+1);fs.append(f if side<0 else tuple(reversed(f)))
  mesh('Ferry original flowing wave '+str(band),vs,fs,ma)
 text_obj('Ferry generic hull label','WATER TRANSIT',(.3,side*4.145,.64),.29,white,side)
 # Tall pink diagonal behind the pilot house, displaced forward at its base.
 shape=[(4.36,1.10),(5.13,1.10),(4.45,4.16),(3.68,4.16)]
 pv=[(x,side*y,z) for y in (3.13,3.49) for x,z in shape]
 pf=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 pillar=mesh('Ferry structural pink diagonal pilot pillar',pv,[tuple(reversed(f)) for f in pf] if side>0 else pf,pink)
 be=pillar.modifiers.new('Rounded pillar edges','BEVEL');be.width=.035;be.segments=2
 no=pillar.modifiers.new('Pillar face normals','WEIGHTED_NORMAL');no.keep_sharp=True
 # Black hanging cylindrical mooring fenders.
 for x in (-9.8,-3.5,6.1,10.5):
  tube('Ferry fender lanyard',(x,side*4.03,1.1),(x,side*4.03,.64),.02,black)
  cyl('Ferry hull rubber fender',(x,side*4.03,.34),.18,.75,rubber,segments=12)
# Raised blue wheelhouse: upper front edge leans forward over the lower blue chest panel.
vs=[(4.35,-3.15,1.08),(8.25,-3.15,1.08),(8.25,3.15,1.08),(4.35,3.15,1.08),(4.35,-3.15,4.80),(9.10,-3.15,4.80),(9.10,3.15,4.80),(4.35,3.15,4.80)]
fs=[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]
pilot=mesh('Ferry raised blue pilot wheelhouse',vs,fs,blue)
# Bold blue rear roof ramp and overhanging eyebrow, visible in side silhouette.
mesh('Ferry raised bridge roof transition',[(3.55,-3.16,4.10),(4.55,-3.16,4.82),(4.55,3.16,4.82),(3.55,3.16,4.10),(4.7,-3.16,4.1),(4.7,3.16,4.1)],[(0,1,2,3),(0,4,1),(3,2,5),(1,4,5,2)],blue)
box('Ferry blue pilot roof eyebrow',(6.78,0,4.88),(5.15,6.72,.22),blue,.12,3)
for low,high in [(-2.95,-1.05),(-.93,.93),(1.05,2.95)]:projected_glass('Ferry forward sloped pilot windscreen',pilot,'X',(low,high),(2.47,4.61),glass,cols=6,rows=8)
for side in (-1,1):
 side_rect('Ferry high pilot side window',6.02,side*3.169,4.22,2.36,.72,.06,glass,side)
 panel('Ferry pilot forward quarter pane',[(7.44,side*3.172,2.51),(8.5,side*3.172,2.51),(8.98,side*3.172,4.60),(7.44,side*3.172,4.60)][::1 if side<0 else -1],glass)
 side_rect('Ferry pilot crew door frame',5.55,side*3.175,2.27,1.04,2.35,.10,steel,side)
 side_rect('Ferry pilot crew door',5.55,side*3.187,2.27,.94,2.23,.08,white,side)
 side_rect('Ferry pilot crew door window',5.55,side*3.198,2.83,.58,.68,.07,glass,side)
 tube('Ferry pilot door handle',(5.82,side*3.215,2.05),(5.82,side*3.215,2.29),.018,steel)
 # Small white service door aft of wheelhouse entry, below the raised roof.
 cyl('Ferry bridge navigation lamp',(8.84,side*3.18,5.03),.075,.14,green if side<0 else red,segments=12)
for y in (-1.9,1.9):tube('Ferry pilot windscreen wiper',project(pilot,'X',y,2.63),project(pilot,'X',y+.5,4.08),.02,black)
# Open squared bow, white guardrails and orange life-saving rings.
for side in (-1,1):
 for x in (8.8,10.0,11.45):tube('Ferry bow rail stanchion',(x,side*3.82,1.09),(x,side*3.82,2.18),.035,white)
 for z in (1.65,2.16):tube('Ferry bow side handrail',(8.8,side*3.82,z),(11.45,side*3.82,z),.035,white)
for y in (-3.82,-2.5,-1.2,0,1.2,2.5,3.82):tube('Ferry bow frontal rail post',(11.45,y,1.09),(11.45,y,2.18),.035,white)
for z in (1.64,2.16):tube('Ferry squared bow frontal rail',(11.45,-3.82,z),(11.45,3.82,z),.035,white)
def lifebuoy(name,loc,axis):
 bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=6,major_radius=.32,minor_radius=.075,location=loc);o=bpy.context.object;o.name=name;o.parent=CURRENT;o.data.materials.append(orange);o.data.materials.append(white)
 for p in o.data.polygons:
  a=math.atan2(p.center.y,p.center.x);p.material_index=1 if abs(math.sin(2*a))<.32 else 0;p.use_smooth=True
 if axis=='X':o.rotation_euler.y=math.pi/2
 else:o.rotation_euler.x=math.pi/2
for side in (-1,1):
 lifebuoy('Ferry bow orange lifebuoy',(11.51,side*2.56,1.7),'X')
 lifebuoy('Ferry quarter orange lifebuoy',(9.9,side*3.87,1.7),'Y')
 box('Ferry bow safety locker',(10.45,side*.85,1.39),(.46,.58,.61),white,.05)
 cyl('Ferry forward mooring bollard',(10.45,side*2.75,1.24),.09,.3,steel,segments=12)
 tube('Ferry forward bollard cap',(10.27,side*2.75,1.39),(10.64,side*2.75,1.39),.045,steel)
# Open stern deck under a squared blue canopy, retaining secondary seating details.
box('Ferry squared blue stern canopy',(-10.26,0,4.17),(3.49,7.16,.20),blue,.10,2)
for side in (-1,1):
 for x in (-11.55,-8.9):tube('Ferry stern canopy support',(x,side*3.31,1.08),(x,side*3.31,4.1),.055,white)
 for x in (-11.4,-10.2,-8.9):tube('Ferry aft guardrail post',(x,side*3.81,1.08),(x,side*3.81,2.05),.03,white)
 tube('Ferry aft handrail',(-11.4,side*3.81,2.03),(-8.9,side*3.81,2.03),.035,white)
 box('Ferry stern passenger bench',(-10.25,side*2.62,1.48),(1.95,.6,.16),white,.06)
 box('Ferry stern seat back',(-10.25,side*2.89,1.81),(1.95,.12,.58),white,.06)
 for x in (-10.85,-9.65):tube('Ferry stern seat leg',(x,side*2.62,1.1),(x,side*2.62,1.41),.045,steel)
box('Ferry aft glass saloon door',(-8.725,0,2.3),(.04,1.45,2.3),glass,.04)
for y in (-3.8,-2.0,0,2.0,3.8):tube('Ferry stern transom rail post',(-11.43,y,1.08),(-11.43,y,2.05),.03,white)
tube('Ferry stern transom handrail',(-11.43,-3.8,2.03),(-11.43,3.8,2.03),.035,white)
# Roof HVAC, life rafts, communication equipment and horns are original generic shapes.
for x in (-6.9,-2.9,1.15):
 box('Ferry roof ventilation unit',(x,0,4.34),(1.4,1.65,.32),white,.11,2)
 for j in range(6):box('Ferry roof vent louvers',(x-.48+j*.19,0,4.505),(.07,1.15,.012),black)
for side in (-1,1):
 for x in (-4.7,.1):
  cyl('Ferry life raft pod',(x,side*2.15,4.37),.20,1.05,white,'X',12)
  for dx in (-.33,.33):box('Ferry life raft restraint',(x+dx,side*2.15,4.37),(.055,.40,.41),steel,.015)
tube('Ferry pilot communications mast',(6.3,0,5.0),(6.3,0,6.13),.04,white)
box('Ferry radar scanner',(6.3,0,5.7),(.16,1.3,.12),white,.04)
cyl('Ferry mast light',(6.3,0,6.17),.055,.12,light,segments=10)
for y in (-.8,.8):
 tube('Ferry horn support',(6.9,y,5.0),(6.9,y,5.26),.025,steel)
 cyl('Ferry bridge horn',(7.12,y,5.28),.075,.42,white,'X',12)
CURRENT=None

# Source keeps meaningful independently editable components and original materials.
bpy.context.scene['asset_note']='Original scenic kit inspired by official visual references. Approximate proportions, not exact CAD. No operator logos.'
for source_root in (train,ferry):
 co=bpy.data.collections.new(source_root.name+' editable parts');bpy.context.scene.collection.children.link(co)
 for obj in [source_root]+list(source_root.children_recursive):
  for old_collection in list(obj.users_collection):old_collection.objects.unlink(obj)
  co.objects.link(obj)
ferry.location.y=18;bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'transit_vehicles.blend'))
ferry.location.y=0;bpy.context.view_layer.update()

# Bake per-part source geometry into one 3-material vertex-color mesh per carriage/ferry.
webmats=[]
for group,rough,metal,em in [('surface',.34,.28,0),('glazing',.15,.36,0),('lamps',.22,0,1.6)]:
 m=bpy.data.materials.new('Transit_'+group.title());m.use_nodes=True;nt=m.node_tree;p=nt.nodes.get('Principled BSDF');col=nt.nodes.new('ShaderNodeVertexColor');col.layer_name='TransitColor';nt.links.new(col.outputs['Color'],p.inputs['Base Color']);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if em:nt.links.new(col.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=em
 webmats.append(m)

def descendants(o):return [x for x in bpy.context.scene.objects if x.parent==o]
def bake(parent,newparent):
 dg=bpy.context.evaluated_depsgraph_get();verts=[];faces=[];colors=[];groups=[];normals=[];smooth=[]
 for o in list(descendants(parent)):
  if o.type not in ('MESH','FONT','CURVE'):continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();xf=parent.matrix_world.inverted()@o.matrix_world;nm=xf.to_3x3().inverted().transposed();base=len(verts);verts.extend([xf@v.co for v in me.vertices])
  for p in me.polygons:
   material=me.materials[p.material_index] if me.materials else white;node=material.node_tree.nodes.get('Principled BSDF');color=tuple(node.inputs['Base Color'].default_value);groups.append({'surface':0,'glazing':1,'lamps':2}.get(material.get('web_group','surface'),0));faces.append(tuple(base+i for i in p.vertices));colors.append(color);smooth.append(p.use_smooth)
   for li in p.loop_indices:normals.append((nm@me.corner_normals[li].vector).normalized())
  ev.to_mesh_clear()
 me=bpy.data.meshes.new(parent.name+'_Optimized');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(parent.name+'_Geometry',me);bpy.context.collection.objects.link(o);o.parent=newparent
 for m in webmats:me.materials.append(m)
 ca=me.color_attributes.new(name='TransitColor',type='FLOAT_COLOR',domain='CORNER')
 for p,gi,col,sm in zip(me.polygons,groups,colors,smooth):
  p.material_index=gi;p.use_smooth=sm
  for li in p.loop_indices:ca.data[li].color=col
 me.normals_split_custom_set(normals)
 return o

bpy.context.view_layer.update();exports=[]
for src,key in [(train,'coast_metro_train'),(ferry,'water_transit_ferry')]:
 if src==train and os.environ.get('TRANSIT_FERRY_ONLY'):
  exports.append(json.loads((OUT/'coast_metro_train_manifest.json').read_text()));continue
 if src==ferry and os.environ.get('TRANSIT_TRAIN_ONLY'):
  exports.append(json.loads((OUT/'water_transit_ferry_manifest.json').read_text()));continue
 nr=empty(src.name+'_WEB');nodes=[]
 if src==train:
  for ci,car in enumerate(cars):
   p=empty('TrainCar_'+str(ci)+'_WEB',tuple(car.location),nr);p.rotation_euler=car.rotation_euler.copy();bake(car,p);nodes.append(p)
 else:bake(src,nr)
 bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');nr.select_set(True)
 for o in nr.children_recursive:o.select_set(True)
 # Temporarily rename source nodes so glTF gets clean stable public API names.
 oldnames=[]
 for o in [src]+(cars if src==train else []):oldnames.append((o,o.name));o.name=o.name+'_SOURCE'
 nr.name=src.name.replace('_SOURCE','')
 for i,p in enumerate(nodes):p.name='TrainCar_'+str(i)
 path=WEB/(key+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_animations=False,export_apply=True,export_yup=True,export_extras=True)
 blob=path.read_bytes();jlen=struct.unpack_from('<I',blob,12)[0];g=json.loads(blob[20:20+jlen]);tri=sum(g['accessors'][p['indices']]['count']//3 for me in g['meshes'] for p in me['primitives']);draws=sum(len(me['primitives']) for me in g['meshes'])
 coords=[o.matrix_world@v.co for o in nr.children_recursive if o.type=='MESH' for v in o.data.vertices];mn=[min(v[i] for v in coords) for i in range(3)];mx=[max(v[i] for v in coords) for i in range(3)]
 manifest={'file':str(path.relative_to(ROOT)),'root':nr.name,'coordinates':'meters; glTF +X forward, +Y up, -Z left','triangles':tri,'draw_calls_per_instance':draws,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest(),'bounds_blender_m':{'min':mn,'max':mx},'dimensions_three_m':[mx[0]-mn[0],mx[2]-mn[2],mx[1]-mn[1]],'materials':[m.name for m in webmats],'geometry':'Original procedural mesh, no photo textures or logos. Scenic vehicle, not physics or operator CAD.'}
 if src==train:manifest.update({'pivot':'rail contact at Three Y=0','gauge_m':1.435,'wheel_center_lateral_m':0.7175,'wheel_contact_width_m':0.16,'wheel_radius_m':0.39,'carriages':[{'node':'TrainCar_'+str(i),'center_offset_x_m':off,'local_rotation_y_rad':0 if i<2 else -math.pi,'length_m':19.4} for i,off in enumerate((19.4,0,-19.4))],'path_contract':'Place TrainCar_i at path(position + center_offset_x_m). Preserve car2 local facing reversal: rotation.y = pathHeading - PI. Root identity, path is Three XZ plane. Bellows are split static collars, no runtime deformation.'})
 else:manifest.update({'pivot':'sea level at Three Y=0; root center x/y=0','revision':2,'reference_basis':'User-provided side and bow Water Metro photographs inspected; raised pilot-house and twin-hull interpretation, no logos.','draft_approx_m':1.12,'hull_length_m':23.5,'wake_sockets_three_m':{'stern_port':[-11.8,0,-3.08],'stern_starboard':[-11.8,0,3.08]},'motion_note':'Move root rigidly; optional gentle roll/heave. Exterior scenic ferry, opaque windows and simplified interior.'})
 if src==ferry:
  manifest['bounds_three_m']={'min':[mn[0],mn[2],-mx[1]],'max':[mx[0],mx[2],-mn[1]]}
  manifest['collision_proxy']={'type':'obb','center_local_m':[(mn[0]+mx[0])/2,(mn[2]+mx[2])/2,-(mn[1]+mx[1])/2],'half_extents_m':[(mx[0]-mn[0])/2,(mx[2]-mn[2])/2,(mx[1]-mn[1])/2],'note':'Conservative full bounds including mast and fenders. A capsule matching only total length/beam misses squared bow corners.'}
 (OUT/(key+'_manifest.json')).write_text(json.dumps(manifest,indent=2));exports.append(manifest)
 for o in [nr]+list(nr.children_recursive):bpy.data.objects.remove(o,do_unlink=True)
 for o,n in oldnames:o.name=n
 print('TRANSIT_EXPORTED',json.dumps(manifest))
(OUT/'manifest.json').write_text(json.dumps({'assets':exports,'reference_sources':[{'url':'https://kochimetro.org/completed-projects/','use':'Visual reference only, actual pixels inspected. No image shipped.'},{'url':'https://cdn-dev.watermetro.co.in/boat_05_b6ae163381.png','use':'Visual reference only, actual pixels inspected. No image shipped.'}],'user_reference_files':['reference-image-not-distributed','reference-image-not-distributed'],'source':'blender/build_transit_vehicles.py','blender':'4.3.2','license_note':'All geometry and palette authored originally for this project; no official insignia or downloaded mesh. Operator references do not imply endorsement.'},indent=2))

t=exports[0];f=exports[1]
j={'version':1,'coordinates':'glTF meters: +X forward, +Y up, -Z left','train':{'asset':'coast_metro_train','file':'coast_metro_train.glb','root':'CoastMetroTrain','carriage_nodes':['TrainCar_0','TrainCar_1','TrainCar_2'],'offsets_m':[19.4,0,-19.4],'local_yaw_rad':[0,0,-3.141592653589793],'root_contact_y_m':0,'gauge_m':t.get('gauge_m',1.435),'wheel_center_lateral_m':t.get('wheel_center_lateral_m',0.7175),'wheel_contact_width_m':t.get('wheel_contact_width_m',0.16),'floor_y_m':1.15,'roof_y_m':4.214,'dimensions_xyz_m':t['dimensions_three_m'],'triangles':t['triangles'],'draw_calls':t['draw_calls_per_instance'],'sha256':t['sha256']},'ferry':{'asset':'water_transit_ferry','file':'water_transit_ferry.glb','root':'WaterTransitFerry','root_contact_y_m':0,'deck_y_m':1.09,'draft_m':1.12,'dimensions_xyz_m':f['dimensions_three_m'],'wake_sockets':f['wake_sockets_three_m'],'bounds_local_m':f.get('bounds_three_m'),'collision_proxy':f.get('collision_proxy'),'revision':f.get('revision',1),'triangles':f['triangles'],'draw_calls':f['draw_calls_per_instance'],'sha256':f['sha256']},'notes':['Original approximate scenic vehicles; not operator CAD or engineering simulation.','No official logos, photo textures or downloaded meshes.','Train rear carriage yaw must include its source -PI rotation.','Bellows are paired end collars for modest bends, not deformable fabric.','Opaque exterior glazing; ferry has simplified open stern seats, no complete passenger interior.']}
(OUT/'transit_vehicle_manifest.json').write_text(json.dumps(j,indent=2));(WEB/'transit_vehicle_manifest.json').write_text(json.dumps(j,indent=2))

# Render the actual exported GLBs, not separate high-detail substitutes.
def aim(o,pt):o.rotation_euler=(Vector(pt)-o.location).to_track_quat('-Z','Y').to_euler()
def light_area(name,loc,power,size,color,target=(0,0,1.8)):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;aim(o,target)
for key in ('coast_metro_train','water_transit_ferry'):
 if key=='coast_metro_train' and os.environ.get('TRANSIT_FERRY_ONLY'):continue
 if key=='water_transit_ferry' and os.environ.get('TRANSIT_TRAIN_ONLY'):continue
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(WEB/(key+'.glb')))
 # Verify imported names and finite geometry against the browser budget.
 validation={'result':'PASS','file':key+'.glb','render_source':'Actual exported GLB reimport','finite_vertices':True,'texture_images':len(json.loads((WEB/(key+'.glb')).read_bytes()[20:20+struct.unpack_from('<I',(WEB/(key+'.glb')).read_bytes(),12)[0]]).get('images',[])),'hierarchy':[]}
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   validation['finite_vertices'] &= all(math.isfinite(c) for v in o.data.vertices for c in v.co)
  if o.type=='EMPTY':validation['hierarchy'].append({'name':o.name,'parent':o.parent.name if o.parent else None,'location':list(o.location)})
 manifest=next(m for m in exports if m['file'].endswith(key+'.glb'));validation['budget_pass']=manifest['triangles']<=(15000 if key=='coast_metro_train' else 12000) and manifest['draw_calls_per_instance']<=9
 if not(validation['finite_vertices'] and validation['budget_pass']):validation['result']='REVIEW'
 (OUT/(key+'_validation.json')).write_text(json.dumps(validation,indent=2))
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=64;scene.cycles.use_denoising=False;scene.render.resolution_x=1440;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
 world=bpy.data.worlds.new('Transit soft studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.23,.29,.34,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.55;scene.world=world
 floor=mat('Preview ground '+key,(.12,.17,.19) if key=='water_transit_ferry' else (.15,.18,.20),.12,.28 if key=='water_transit_ferry' else .55)
 bpy.ops.mesh.primitive_plane_add(size=400,location=(0,0,0 if key=='water_transit_ferry' else -.035));bpy.context.object.name='Preview water' if key=='water_transit_ferry' else 'Preview ground';bpy.context.object.data.materials.append(floor)
 if key=='coast_metro_train':
  # Simple neutral presentation rails; not exported station/course geometry.
  for y in (-.7175,.7175):box('Preview rail',(0,y,.015),(70,.075,.05),steel,.01)
  for x in range(-34,35,1):box('Preview rail sleeper',(x,0,-.015),(.18,2.5,.08),black,.015)
 light_area('Long softbox',(5,-14,28),22000,24,(.83,.91,1));light_area('Warm rear edge',(-22,10,16),16000,20,(1,.91,.78));light_area('Cab soft fill',(34,8,10),0 if key=='coast_metro_train' else 12000,16,(.8,.94,1))
 cd=bpy.data.cameras.new('Transit preview camera');cam=bpy.data.objects.new('Transit preview camera',cd);bpy.context.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO'
 shots=[('front',(43,-42,26),(0,0,1.6),61),('cab',(37,-19,11),(20,0,2),25)] if key=='coast_metro_train' else [('front',(30,-39,15),(0,0,2.0),34),('stern',(-25,-30,13),(-.3,0,2.0),32)]
 for tag,loc,target,scale in shots:
  cam.location=loc;cd.ortho_scale=scale;aim(cam,target);scene.render.filepath=str(OUT/(key+('_reference_refined_' if key=='water_transit_ferry' else '_preview_')+tag+'.png'))
  if not os.environ.get('TRANSIT_SKIP_RENDER'):bpy.ops.render.render(write_still=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(key+'_preview.blend')))
print('TRANSIT_KIT_READY')
