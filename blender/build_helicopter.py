"""Original light-twin helicopter kit; primary references inform proportions only.
No manufacturer replication claim, logos, photographs or third-party geometry.
"""
import bpy,math,json,hashlib,shutil,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'assets/helicopter';W=R/'assets/web';P=R/'web/public/assets'
for p in (O,W,P):p.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'blender'));import rebuild_car_helpers as h
sys.path.insert(0,str(O));from cleanup_helicopter_glb import clean

def sphere(name,loc,scale,mat,segments=20,rings=12):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=loc);ob=bpy.context.object;ob.name=name;ob.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.data.materials.append(mat)
 for q in ob.data.polygons:q.use_smooth=True
 if h.CURRENT:h.parent_keep(ob,h.CURRENT)
 return ob

def text(label,loc,size,mat,side):
 cu=bpy.data.curves.new('Original generic marking '+label,'FONT');cu.body=label;cu.size=size;cu.extrude=.001;cu.bevel_depth=0;cu.resolution_u=2;cu.align_x='CENTER';cu.align_y='CENTER';ob=bpy.data.objects.new('Generic '+label+(' left'if side>0 else' right'),cu);bpy.context.scene.collection.objects.link(ob);cu.materials.append(mat);ob.location=loc
 # Text's X axis follows the side of the airframe, with local normal outboard.
 ob.rotation_euler=(math.pi/2,0,0) if side<0 else (math.pi/2,0,math.pi)
 h.parent_keep(ob,h.CURRENT);return ob

rows=[(-2.55,.08,1.65,.12),(-2.28,.40,1.55,.40),(-1.88,.72,1.53,.68),(-1.30,.87,1.57,.82),(-.55,.91,1.59,.88),(.2,.91,1.58,.91),(.9,.86,1.57,.88),(1.50,.75,1.50,.76),(2.02,.56,1.40,.58),(2.43,.29,1.30,.30),(2.65,.025,1.25,.05)]
def surf(x,a,offset=0):
 width,z,hh=h.smooth_interp(rows,x);return Vector((x,(width+offset)*math.cos(a),z+(hh+offset)*math.sin(a)))

for police in (False,True):
 h.reset();key='police'if police else'civilian';D=O/key;D.mkdir(exist_ok=True)
 paint=h.material('Helicopter ceramic white airframe',(.72,.77,.78),metal=.18,rough=.32,coat=.32)
 accent=h.material('Helicopter police navy'if police else'Helicopter civilian petrol teal',(.018,.045,.10)if police else(.015,.16,.18),metal=.25,rough=.30,coat=.40)
 dark=h.material('Helicopter graphite composite',(.018,.024,.030),metal=.10,rough=.53)
 metal=h.material('Helicopter brushed titanium',(.29,.34,.36),metal=.82,rough=.29)
 glass=h.material('Helicopter smoke canopy glazing',(.052,.13,.17),metal=.04,rough=.10,alpha=.50,coat=.60)
 red=h.material('Helicopter red navigation lamp',(.95,.015,.008),rough=.20,emit=3)
 green=h.material('Helicopter green navigation lamp',(.012,.62,.08),rough=.20,emit=3)
 white=h.material('Helicopter white optical lens',(.68,.82,.96),metal=.18,rough=.15,emit=.8)
 blue=h.material('Helicopter police blue beacon',(.015,.14,.95),rough=.20,emit=3)if police else white
 root=h.empty('HELICOPTER_ROOT');body=h.empty('Airframe',parent=root);main=h.empty('MainRotor',(-.35,0,3.35),root);tail=h.empty('TailRotor',(-6.75,0,2.0),root)
 yaw=h.empty('SearchlightYaw',(1.45,0,.60),root);pitch=h.empty('SearchlightPitch',parent=yaw);socket=h.empty('SearchlightSocket',(0,0,-.25),pitch)
 navs=[h.empty('NavPortSocket',(-1.25,1.03,1.52),root),h.empty('NavStarboardSocket',(-1.25,-1.03,1.52),root),h.empty('NavTailSocket',(-7.18,0,3.47),root),h.empty('BeaconSocket',(-.97,0,2.96),root)]
 groups=[root,body,main,tail,yaw,pitch,socket]+navs;h.CURRENT=body
 # Smooth loft with actual glazed surface openings: no opaque shell behind windows.
 xs=sorted(set([round(-2.55+i*5.20/64,7)for i in range(65)]+[-1.68,-.94,-.83,.42,.72]));angles=sorted(set([i*math.tau/56-math.pi/2 for i in range(57)]+[-.08,.64,math.pi-.64,math.pi+.08]));parts={}
 for i in range(len(xs)-1):
  for j in range(len(angles)-1):
   x=(xs[i]+xs[i+1])/2;a=(angles[j]+angles[j+1])/2;aa=a%(math.tau);window=(x>.72 and -.08<a<math.pi+.08)or((-1.68<x<-.94 or -.83<x<.42)and(-.08<a<.64 or math.pi-.64<a<math.pi+.08))
   lower=(math.sin(a)<(-.08 if police else -.48));ma=glass if window else(accent if lower else paint);vs,fs=parts.setdefault(ma,([],[]));q=len(vs);vs.extend([surf(xx,an)for xx,an in[(xs[i],angles[j]),(xs[i+1],angles[j]),(xs[i+1],angles[j+1]),(xs[i],angles[j+1])]]);fs.append((q,q+1,q+2,q+3))
 for ma,(vs,fs)in parts.items():
  # Weld shared vertices so manufactured shell has genuinely smooth curvature.
  ob=h.mesh('Lofted monocoque '+ma.name,vs,fs,ma,True)
  import bmesh
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.to_mesh(ob.data);bm.free()
 for xx in [rows[0][0],rows[-1][0]]:h.mesh('Closed airframe end', [surf(xx,a)for a in angles[:-1]],[tuple(range(len(angles)-1))],paint,True)
 # Glazing seals and central windscreen divider, real narrow geometry.
 for a in[-.08,math.pi+.08]:h.line('Canopy lower gasket',[surf(x,a,.008)for x in xs if x>=.72],.013,dark,6)
 h.line('Canopy rear gasket',[surf(.72,a,.008)for a in angles if -.08<=a<=math.pi+.08],.014,dark,6)
 h.line('Windscreen central structural strip',[surf(x,math.pi/2,.011)for x in xs if x>=.72],.026,paint,8)
 for x0,x1 in[(-1.68,-.94),(-.83,.42)]:
  for aa,bb in[(-.08,.64),(math.pi-.64,math.pi+.08)]:
   edge=[surf(x0,aa+(bb-aa)*i/8,.012)for i in range(9)]+[surf(x0+(x1-x0)*i/8,bb,.012)for i in range(1,9)]+[surf(x1,bb+(aa-bb)*i/8,.012)for i in range(1,9)]+[surf(x1+(x0-x1)*i/8,aa,.012)for i in range(1,9)]
   h.line('Cabin window rubber seal',edge,.012,dark,6)
 # Cabin doors/panel seams follow the body, not flat decals.
 for side in(-1,1):
  a=0 if side>0 else math.pi
  for xx in[-1.82,-.90,.55]:h.line('Door vertical seam',[surf(xx,a+side*(-.95+i*1.73/20),.006)for i in range(21)],.004,dark,5)
  h.line('Lower cabin sill',[surf(-1.82+i*2.37/16,a-side*.76,.006)for i in range(17)],.004,dark,5)
  for xx in[-1.35,.1]:
   v=surf(xx,a-side*.19,.025);h.line('Recessed door handle',[v+Vector((-.095,0,0)),v+Vector((.095,0,0))],.018,metal,8)
  # Contrasting narrow side stripe below the clear windows.
  pts=[surf(xx,a-side*.37,.015)for xx in[-2.08,-1.6,-1,-.4,.2,.9,1.5,2.0]]
  h.line('Swept livery accent',pts,.035,accent,6)
  text('POLICE'if police else'COAST AIR',(-.42,side*.925,1.37),.205,paint if police else accent,side)
  # Skid tubes with rising noses and two smooth cross arches.
  h.line('Landing skid runner',[(-2.07,side*1.10,.16),(-1.96,side*1.10,.065),(-1.45,side*1.10,.065),(1.6,side*1.10,.065),(1.9,side*1.10,.17),(2.1,side*1.10,.38)],.065,metal,12)
  for xx in[-1.2,1.15]:h.line('Landing gear curved strut',[(xx,side*.55,.87),(xx,side*.80,.69),(xx,side*1.05,.31),(xx,side*1.10,.09)],.052,metal,10)
  h.line('Cabin access step',[(-.62,side*.90,.68),(-.62,side*1.12,.48),(.2,side*1.12,.48),(.2,side*.90,.68)],.026,metal,8)
  for xx in[-1.1,.8]:h.box('Skid wear pad',(xx,side*1.1,.031),(.32,.15,.035),dark,.007)
 # Interior with six individual seats, console and flight controls, visible through canopy.
 h.box('Cabin flat interior floor',(-.1,0,.94),(2.8,.96,.04),dark,.015)
 h.mesh('Fitted aft cabin bulkhead',[surf(-1.84,j*math.tau/48,-.03)for j in range(48)],[tuple(range(48))],dark,False)
 for x in[-1.05,-.15,.88]:
  for y in[-.40,.40]:
   h.box('Seat mounting pedestal',(x,y,.98),(.25,.25,.05),dark,.012)
   h.box('Individual seat cushion',(x,y,1.08),(.47,.43,.16),dark,.065);ob=h.box('Upholstered seat back',(x-.22,y,1.36),(.13,.45,.60),dark,.065);ob.rotation_euler.y=-.10
   h.box('Seat head restraint',(x-.25,y,1.74),(.12,.30,.16),dark,.04)
 h.box('Instrument panel housing',(1.51,0,1.45),(.28,1.22,.32),dark,.045)
 for y in[-.37,0,.37]:h.box('Unbranded glass flight display',(1.667,y,1.50),(.012,.28,.18),glass,.006)
 for y in[-.40,.40]:
  h.line('Cyclic flight control',[(.91,y,.89),(.98,y,1.12),(1.06,y,1.17)],.018,dark,8)
  for sy in[-.10,.10]:h.box('Anti torque pedal',(1.32,y+sy,1.04),(.12,.09,.04),metal,.004)
 # Twin engine nacelles, vents and two physically open exhaust rims.
 for side in[-1,1]:
  sphere('Twin turbine cowling',(-.90,side*.42,2.56),(1.05,.34,.29),paint,24,12)
  sphere('Dark forward engine intake',(.16,side*.42,2.57),(.018,.225,.155),dark,20,10)
  h.torus('Engine exhaust metal lip',(-1.99,side*.40,2.59),.145,.026,metal,'X',24,8)
  h.cylinder('Deep exhaust shadow',(-1.98,side*.40,2.59),.128,.018,dark,'X',24)
  pipe=[(xx,side*.40+.145*math.cos(j*math.tau/24),2.59+.145*math.sin(j*math.tau/24))for xx in[-1.99,-1.75]for j in range(24)]
  h.mesh('Open exhaust neck',pipe,[(j,(j+1)%24,(j+1)%24+24,j+24)for j in range(24)],metal,True)
  for k in range(7):h.box('Turbine side ventilation slot',(-.95+k*.10,side*.728,2.56),(.045,.012,.12),dark,.005)
 h.cylinder('Main gearbox shroud',(-.35,0,2.81),.30,.40,paint,'Z',32);h.cylinder('Main rotor fixed mast',(-.35,0,3.10),.075,.40,metal,'Z',24)
 # Tapering structural tail boom.
 br=[(-2.05,.34,1.72),(-2.65,.29,1.83),(-3.6,.23,1.91),(-4.7,.18,1.98),(-5.8,.15,2.02),(-5.98,.16,2.02)]
 vs=[];fs=[]
 for x,rr,z in br:
  for j in range(20):a=j*math.tau/20;vs.append((x,rr*math.cos(a),z+rr*math.sin(a)))
 for i in range(len(br)-1):
  for j in range(20):q=i*20+j;fs.append((q,i*20+(j+1)%20,(i+1)*20+(j+1)%20,q+20))
 h.mesh('Tapered tail boom',vs,fs,paint,True)
 for x,rr,z in[br[2],br[4]]:h.torus('Tail service panel ring',(x,0,z),rr+.003,.008,metal,'X',20,5)
 # Horizontal stabiliser and elegant swept fin, distinct original silhouette.
 for side in[-1,1]:
  h.mesh('Tapered horizontal stabiliser',[(-5.05,0,2.05),(-4.38,0,2.05),(-4.68,side*1.25,2.10),(-5.18,side*1.25,2.10),(-5.05,0,1.99),(-4.38,0,1.99),(-4.68,side*1.25,2.04),(-5.18,side*1.25,2.04)],[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],accent,False)
 # Annular shrouded tail rotor duct, real hole and radial width.
 profile=[(-.18,.69),(-.19,.77),(-.13,.89),(.13,.89),(.19,.77),(.18,.69)];vs=[];fs=[]
 for y,rr in profile:
  for j in range(48):a=j*math.tau/48;vs.append((-6.75+rr*math.cos(a),y,2+rr*math.sin(a)))
 for i in range(len(profile)):
  for j in range(48):q=i*48+j;fs.append((q,i*48+(j+1)%48,((i+1)%len(profile))*48+(j+1)%48,((i+1)%len(profile))*48+j))
 h.mesh('Shrouded anti torque duct',vs,fs,paint,True)
 # Fin behind duct merges visually with its top rather than blocking its opening.
 outline=[(-6.22,2.63),(-6.63,3.49),(-7.29,3.49),(-7.52,2.22),(-7.49,1.63),(-7.05,1.27),(-6.25,1.33)]
 # Upper portion only; annular housing below is deliberately open.
 outline=[(-6.24,2.70),(-6.65,3.48),(-7.31,3.48),(-7.19,2.72)]
 vs=[(x,y,z)for y in[-.09,.09]for x,z in outline];n=len(outline);h.mesh('Swept vertical tail fin',vs,[tuple(reversed(range(n))),tuple(n+i for i in range(n))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)],accent,False)
 for j in range(3):
  a=j*math.tau/3;h.line('Stationary tail rotor bearing support',[(-6.75+.11*math.cos(a),.145,2+.11*math.sin(a)),(-6.75+.68*math.cos(a),.145,2+.68*math.sin(a))],.022,metal,6)
 h.cylinder('Stationary tail bearing',(-6.75,.14,2),.11,.10,metal,'Y',20)
 # Small visible antennas/pitots and nav lamps—not opaque billboard details.
 h.line('Dorsal antenna',[(-1.3,0,2.86),(-1.48,0,3.07)],.014,dark,6)
 for side in[-1,1]:
  h.line('Nose pitot probe',[(2.18,side*.36,1.31),(2.63,side*.36,1.29)],.012,metal,6)
  h.box('Navigation light mount',(-1.25,side*.95,1.52),(.18,.16,.07),paint,.015)
  sphere('Port red navigation'if side>0 else'Starboard green navigation',(-1.25,side*1.03,1.52),(.065,.035,.035),red if side>0 else green,12,8)
 sphere('Tail white marker',(-7.18,0,3.47),(.05,.05,.045),white,12,8)
 sphere('Dorsal anti collision beacon',(-.97,0,2.96),(.07,.07,.055),blue if police else red,12,8)
 if police:
  for side in[-1,1]:sphere('Side police blue beacon',(-.65,side*.87,2.14),(.11,.045,.065),blue,16,8)
 # Rotor blade meshes are attached only to independently animated pivots.
 h.CURRENT=main;h.cylinder('Rotating main hub',(-.35,0,3.35),.25,.13,metal,'Z',24)
 for j in range(4):
  angle=j*math.pi/2+.30;d=Vector((math.cos(angle),math.sin(angle),0));t=Vector((-d.y,d.x,0));origin=Vector((-.35,0,3.35));vs=[];fs=[]
  for radius,chord,sweep,zz in[(.20,.16,0,.0),(.65,.25,0,.015),(3.7,.23,.10,.025),(4.75,.19,.18,.04),(5.1,.13,.34,.055)]:
   for yy,zv in[(-.5,0),(-.12,.018),(.45,.006),(.5,-.008),(-.15,-.018)]:vs.append(origin+d*radius+t*(sweep+chord*yy)+Vector((0,0,zz+zv)))
  for i in range(4):
   for k in range(5):q=i*5+k;fs.append((q,i*5+(k+1)%5,(i+1)*5+(k+1)%5,q+5))
  fs.extend([tuple(reversed(range(5))),tuple(20+i for i in range(5))]);h.mesh('Tapered composite main blade '+str(j),vs,fs,dark,True)
  for rad in[.43,.58]:sphere('Rotor blade root bolt',origin+d*rad+Vector((0,0,.028)),(.025,.025,.018),metal,10,6)
 h.CURRENT=tail;h.cylinder('Rotating anti torque hub',(-6.75,0,2),.12,.11,metal,'Y',20)
 for j in range(10):
  a=j*math.tau/10+.09;d=Vector((math.cos(a),0,math.sin(a)));t=Vector((-math.sin(a),0,math.cos(a)));o=Vector((-6.75,0,2));vs=[]
  for r,chord,sweep in[(.11,.06,0),(.34,.14,.05),(.62,.105,.10)]:
   vs.extend([o+d*r+t*(sweep-chord/2)+Vector((0,-.025,0)),o+d*r+t*(sweep+chord/2)+Vector((0,.025,0))])
  h.mesh('Swept anti torque blade '+str(j),vs,[(0,1,3,2),(2,3,5,4)],dark,False);dark['double_sided']=True
 # Gimbal yoke fixed to yaw node, lamp housing pitched independently.
 h.CURRENT=body;h.cylinder('Searchlight body mount',(1.45,0,.70),.055,.14,metal,'Z',16)
 h.CURRENT=yaw
 for side in[-1,1]:h.line('Searchlight gimbal yoke',[(1.45,side*.24,.67),(1.45,side*.24,.50),(1.45,side*.17,.47)],.025,metal,8)
 h.CURRENT=pitch;h.cylinder('Searchlight cylindrical housing',(1.45,0,.48),.18,.22,dark,'Z',24);h.torus('Searchlight optical bezel',(1.45,0,.365),.15,.027,metal,'Z',24,8);h.cylinder('Searchlight actual lens',(1.45,0,.364),.145,.008,white,'Z',24)
 h.CURRENT=None;bpy.context.view_layer.update()
 root['provenance']='Original project geometry; reuse license not selected by owner. Fictional light-twin kit, not manufacturer CAD.'
 native=D/('Coastal_Twin_'+key.title()+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(native))
 m={'id':'helicopter_'+key,'display_name':'Coastal Twin '+('Police'if police else'Civilian'),'original_fictional_design':True,'native_source':str(native.relative_to(R)),'generator':'blender/build_helicopter.py','coordinate_contract':{'forward':'+X','up':'+Y','left':'-Z','units':'metres','root':'HELICOPTER_ROOT','root_ground_y':0},'rotors':{'main':{'node':'MainRotor','pivot_three':[-.35,3.35,0],'axis_three':[0,1,0],'blade_count':4,'nominal_radius_m':5.1},'tail':{'node':'TailRotor','pivot_three':[-6.75,2,0],'axis_three':[0,0,-1],'blade_count':10,'nominal_radius_m':.62}},'searchlight':{'yaw_node':'SearchlightYaw','pitch_node':'SearchlightPitch','socket_node':'SearchlightSocket','socket_three':[1.45,.35,0],'default_direction_three':[0,-1,0],'yaw_axis_three':[0,1,0],'pitch_forward_axis_three':[0,0,1],'recommended_pitch_limit_rad':.70,'socket_emits_light':False,'note':'Runtime must attach real spotlight at socket and aim at car; geometric lens emission is not a projected beam.'},'navigation_sockets':{'NavPortSocket':[-1.25,1.52,-1.03],'NavStarboardSocket':[-1.25,1.52,1.03],'NavTailSocket':[-7.18,3.47,0],'BeaconSocket':[-.97,2.96,0]},'native_editable_mesh_parts':len([o for o in bpy.data.objects if o.type=='MESH']),'provenance':'Original project geometry; reuse license not selected by owner. Primary Airbus references for general proportions only; no logos/photos/downloaded mesh in outputs.','limitations':['Fictional cinematic game helicopter, not airworthy CAD or verified manufacturer replica.','No physics, AI pursuit, spotlight projection, audio or motion is baked; runtime integration is separate.']}
 # Runtime camera/collision queries must use swept rotor envelope, not just parked blade AABB.
 extent={}
 for tag,group,axis in [('main',main,'Z'),('tail',tail,'Y')]:
  ps=[group.matrix_world.inverted()@(o.matrix_world@v.co)for o in group.children if o.type=='MESH'for v in o.data.vertices]
  rr=max(math.hypot(v.x,v.y if axis=='Z'else v.z)for v in ps);extent[tag]=rr;m['rotors'][tag]['measured_swept_radius_m']=rr
 m['swept_bounds_three_m']={'min':[-7.64,0,-extent['main']],'max':[-.35+extent['main'],3.515,extent['main']]}
 m['optional_blur_asset']={'file':'helicopter_rotor_blur.glb','root':'HelicopterBlurRoot','main_node':'MainRotorBlur','tail_node':'TailRotorBlur','note':'Optional separate transparent geometry. Add at identical root transform; hide at stopped rotor and choose solid/blur visibility in runtime. No automatic animation.'}
 out=D/('helicopter_'+key+'.glb');h.export_glb(groups,out,m);clean(out,m)
 for target in[W/out.name,P/out.name]:shutil.copy2(out,target)
 for target in[D/'manifest.json',W/('helicopter_'+key+'_manifest.json'),P/('helicopter_'+key+'_manifest.json')]:target.write_text(json.dumps(m,indent=2)+'\n')
 print('HELICOPTER_NATIVE_EXPORT_READY',key,json.dumps({k:m[k]for k in['sha256','bytes','triangles','draw_calls','materials','bounds_three_m']}),flush=True)

# Separate optional low-cost authored rotor-blur LOD; never rendered by default in base assets.
h.reset();root=h.empty('HelicopterBlurRoot');main=h.empty('MainRotorBlur',(-.35,0,3.35),root);tail=h.empty('TailRotorBlur',(-6.75,0,2),root);ma=h.material('Helicopter optional rotor blur',(.09,.11,.12),rough=.75,alpha=.10);ma['double_sided']=True
for node,center,rmin,rmax,n,plane in[(main,Vector((-.35,0,3.35)),.28,5.12,64,'XY'),(tail,Vector((-6.75,0,2)),.10,.64,32,'XZ')]:
 h.CURRENT=node;vs=[];fs=[]
 for rr in[rmin,rmax]:
  for j in range(n):
   a=j*math.tau/n;vs.append(center+(Vector((rr*math.cos(a),rr*math.sin(a),0))if plane=='XY'else Vector((rr*math.cos(a),0,rr*math.sin(a)))))
 for j in range(n):fs.append((j,(j+1)%n,(j+1)%n+n,j+n))
 h.mesh('Original optional blur annulus '+node.name,vs,fs,ma,False)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Rotor_Blur_LOD.blend'));m={'id':'helicopter_rotor_blur','purpose':'Optional transparent main/tail rotor annuli, no motion or default visibility baked. Align root with base helicopter.','native_source':'assets/helicopter/Rotor_Blur_LOD.blend','provenance':'Original project geometry; reuse license not selected by owner.'};out=O/'helicopter_rotor_blur.glb';h.export_glb([root,main,tail],out,m);clean(out,m)
for target in[W/out.name,P/out.name]:shutil.copy2(out,target)
for target in[O/'rotor_blur_manifest.json',W/'helicopter_rotor_blur_manifest.json',P/'helicopter_rotor_blur_manifest.json']:target.write_text(json.dumps(m,indent=2)+'\n')
print('HELICOPTER_BLUR_READY',m['triangles'],m['draw_calls'],flush=True)
