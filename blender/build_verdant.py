"""Fresh reconstruction of original Verdant Canopy GT after unpublished V12 source loss.
Recovered green-car photograph and previous preview inform silhouette only.
"""
import sys,math,json,hashlib,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import bpy
from mathutils import Vector
import rebuild_car_helpers as h
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/cars/verdant';WEB=ROOT/'assets/web';PUBLIC=ROOT/'web/public/assets'
for p in(OUT,WEB,PUBLIC):p.mkdir(parents=True,exist_ok=True)
h.reset();paint=h.material('Crimson multi-coat | original fan concept',(.15,.31,.105),.58,.24,coat=.48);carbon=h.material('Verdant | satin exposed aero carbon',(.009,.014,.016),.22,.37,coat=.13);carbon['double_sided']=True
glass=h.material('Verdant | curved smoke canopy glazing',(.025,.055,.052),.16,.11,alpha=.38,coat=.3);lampglass=h.material('Verdant | projector optical cover',(.012,.020,.025),0,.10,alpha=.16,coat=.10);alloy=h.material('Verdant | dark champagne forged alloy',(.22,.24,.18),.85,.26);rubber=h.material('Tire rubber | verdant compound',(.009,.012,.013),0,.78);interior=h.material('Verdant | forest charcoal suede',(.018,.026,.022),0,.86);white=h.material('Verdant | white projector light guides',(.76,.92,1),.12,.20,emit=2.3);red=h.material('LED ruby red | verdant rear lamps',(.40,.004,.009),.1,.24,emit=.7)
root=h.empty('CAR_ROOT');body=h.empty('CarBody',parent=root);hood=h.empty('Hood',parent=body);wing=h.empty('RearWing',(-2.03,0,.85),body);doors={n:h.empty('Door_'+n,parent=body)for n in('Left','Right')};groups=[root,body,hood,doors['Left'],doors['Right'],wing];h.CURRENT=body
rows=[(-2.37,.86,.64,.70),(-2.19,1.00,.71,.80),(-1.85,1.065,.78,.91),(-1.35,1.085,.84,.96),(-1.02,1.01,.83,.92),(-.72,.935,.77,.87),(-.20,.90,.74,.79),(.35,.915,.74,.78),(.80,.98,.73,.79),(1.15,1.04,.67,.84),(1.40,1.065,.62,.855),(1.75,1.035,.55,.79),(2.08,.98,.51,.68),(2.31,.88,.49,.56)]
def prop(x):return h.smooth_interp(rows,x)
def top(x,y):
 w,c,f=prop(x);q=min(1.02,abs(y)/w);a=min(1,q/.80);a=a*a*(3-2*a);return c+(f-c)*a-.10*max(0,(q-.89)/.11)**1.5

def sweep(x,y):
 w,c,f=prop(x)
 if x>1.88:return x-.115*min(1,(x-1.88)/.43)*(abs(y)/w)**2
 if x<-1.95:return x+.10*min(1,(-x-1.95)/.42)*(abs(y)/w)**2
 return x
xs=[-2.37+4.68*i/90 for i in range(91)];v=[];f=[];N=36
for x in xs:
 w,c,a=prop(x);ring=[(w*(-1+2*j/28),top(x,w*(-1+2*j/28)))for j in range(29)]+[(w,a-.20),(w*.98,.34),(w*.86,.16),(0,.14),(-w*.86,.16),(-w*.98,.34),(-w,a-.20)];v.extend((sweep(x,y),y,z)for y,z in ring)
for i in range(len(xs)-1):
 for j in range(N):f.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
f.extend([tuple(reversed(range(N))),tuple((len(xs)-1)*N+j for j in range(N))]);shell=h.mesh('Verdant continuous organic upper monocoque',v,f,paint,True);tri=shell.modifiers.new('Stable boolean foundation','TRIANGULATE');h.apply_mod(shell,tri)
for x in(-1.35,1.35):
 bpy.ops.mesh.primitive_cylinder_add(vertices=80,radius=.449,depth=3,location=(x,0,.368),rotation=(math.pi/2,0,0));h.cut(shell,bpy.context.object,'Actual exposed wheel arch')
h.cut(shell,h.box('Temporary deep canopy aperture',(-.20,0,1.02),(2.03,1.24,1.47),carbon,0),'Open canopy cockpit')
# Genuine deep side tunnels and diagonal flying buttresses, unlike the Vermilion's full door sides.
for s in(-1,1):
 poly=[(.90,.15),(.75,.62),(.22,.67),(-.50,.73),(-.82,.77),(-.97,.15)];vv=[(x,y,z)for y in(s*.645,s*1.30)for x,z in poly];n=len(poly);ff=[tuple(range(n)),tuple(reversed(range(n,2*n)))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)];h.cut(shell,h.mesh('Temporary open side tunnel',vv,ff,carbon,False),'Open side aerodynamic channel')
 h.panel('Dark recessed inner tunnel wall',lambda t,u,sg=s:(.84-1.76*t,sg*(.625+.035*math.sin(math.pi*t)),.255+u*(.34+.12*t)),24,9,carbon,normal_hint=(0,s,0));h.panel('Swept lower tunnel floor',lambda t,u,sg=s:(.84-1.80*t,sg*(.63+.39*u),.205+.022*math.sin(math.pi*t)+.035*u*u),25,12,carbon)
 h.line('Tunnel exposed carbon outer sill',[(.84,s*1.00,.215),(.36,s*1.02,.21),(-.30,s*1.045,.22),(-.95,s*1.06,.25)],.024,carbon,8);h.line('Tunnel upper green knife edge',[(.79,s*.972,.65),(.25,s*.934,.70),(-.43,s*.956,.76),(-.89,s*1.027,.83)],.011,paint,7)
 p=h.panel('Tapered diagonal rear flying buttress',lambda t,u,sg=s:((-.50-.72*t)*(1-u)+(-.72-.16*t)*u,sg*(.94+.13*t+.010*math.sin(math.pi*u)),(.80+.14*t)*(1-u)+(.65-.29*t)*u),12,8,paint,normal_hint=(0,s,.2));so=p.modifiers.new('Actual buttress composite thickness','SOLIDIFY');so.thickness=.014
# Smooth broad bonnet, cut under its exact outline rather than floating over the body.
def hw(x):
 if x<1.83:return .61+.01*(x-.81)/1.02
 if x<2.20:return .62-.32*(x-1.83)/.37
 return max(.001,.30*(2.27-x)/.07)
edge=[.81+1.46*i/48 for i in range(49)];outline=[(sweep(x,-hw(x)),-hw(x))for x in edge]+[(sweep(x,hw(x)),hw(x))for x in reversed(edge)];h.cut(shell,h.prism('Temporary exact bonnet opening',outline,.39,1.6,carbon),'Separate flowing bonnet boundary');h.CURRENT=hood

def bonnet(t,u):
 x=.81+1.46*t;y=(u*2-1)*hw(x);return(sweep(x,y),y,top(x,y)+.003)
p=h.panel('Separate flowing verdant bonnet',bonnet,36,22,paint);so=p.modifiers.new('Formed bonnet skin','SOLIDIFY');so.thickness=.010
for s in(-1,1):h.line('Fine bonnet lateral seam',[bonnet(i/35,0 if s<0 else 1)for i in range(36)],.0023,carbon,5)
h.CURRENT=body
# Broad horizontal front vanes around an actual open full-width radiator mouth.
yz=[(-.88,.235),(-.82,.36),(-.67,.445),(0,.455),(.67,.445),(.82,.36),(.88,.235),(.58,.165),(0,.155),(-.58,.165)];vv=[(x,y,z)for x in(1.98,2.65)for y,z in yz];n=len(yz);ff=[tuple(range(n)),tuple(reversed(range(n,2*n)))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)];h.cut(shell,h.mesh('Temporary low broad mouth',vv,ff,carbon,False),'Open horizontal front radiator mouth');h.mesh('Deep front radiator dark core',[(1.995,y,z)for y,z in yz],[tuple(range(n))],carbon,False,normal_hint=(1,0,0))
for z,half in[(.20,.73),(.267,.83),(.334,.79),(.398,.70)]:
 pts=[]
 for j in range(33):y=half*(-1+2*j/32);pts.append((2.26-.11*(abs(y)/.88)**2,y,z+.020*(abs(y)/.88)**2))
 h.line('Curved horizontal radiator metal vane',pts,.0065,alloy,7)
for y in(-.63,-.32,0,.32,.63):h.line('Dark grille vane support',[(2.205,y,.18),(2.205,y,.43)],.005,carbon,6)
h.prism('Low sculpted carbon front splitter',[(2.40,0),(2.31,.65),(2.18,1.01),(1.98,1.005),(2.04,.69),(2.13,0),(2.04,-.69),(1.98,-1.005),(2.18,-1.01),(2.31,-.65)],.10,.132,carbon)
# Original oval/teardrop optical pods, not the red car's long blade housings.
def lens(name,s,mat,dz):
 cx=1.69;cy=s*.835;vv=[(cx,cy,top(cx,cy)+dz)];ff=[];rings=8;N=48
 for k in range(1,rings+1):
  r=k/rings
  for j in range(N):a=2*math.pi*j/N;x=cx+.355*r*math.cos(a);y=cy+s*.112*r*math.sin(a)*(1+.16*math.cos(a));vv.append((sweep(x,y),y,top(x,y)+dz+.010*(1-r*r)))
 for j in range(N):ff.append((0,1+j,1+(j+1)%N))
 for k in range(rings-1):
  for j in range(N):a=1+k*N+j;b=1+k*N+(j+1)%N;ff.append((a,b,b+N,a+N))
 return h.mesh(name,vv,ff,mat,True,normal_hint=(0,0,1))
for s in(-1,1):
 lens('Teardrop dark optical well',s,carbon,.012);lens('Thin oval optical glazing',s,lampglass,.030)
 for x,yoff,r in[(1.81,-.018,.042),(1.62,.009,.035)]:
  y=s*(.835+yoff);z=top(x,y)+.021;h.torus('Machined oval projector bezel',(sweep(x,y),y,z),r,.006,alloy,'Z',32,6);h.cylinder('White optical projector',(sweep(x,y),y,z+.005),r*.66,.006,white,'Z',32)
 pts=[]
 for j in range(32):a=.40+1.40*j/31;x=1.69+.325*math.cos(a);y=s*(.835+.093*math.sin(a)*(1+.16*math.cos(a)));pts.append((sweep(x,y),y,top(x,y)+.033))
 h.line('Short curved white perimeter light',pts,.0045,white,6)
# Tall gently curved glass canopy and separate fixed glazed door panels.
def wind(t,u):
 q=u*2-1;return(.79-1.02*t,q*(.585-.095*t),(.768-.030*q*q)*(1-t)+(1.225-.065*q*q)*t+.065*math.sin(math.pi*t)*(1-.25*q*q))
def roof(t,u):
 q=u*2-1;return(-.23-.78*t,q*(.490-.085*t),1.225+.040*math.sin(math.pi*t)-.095*t-.065*q*q)
def aft(t,u):
 q=u*2-1;return(-1.01-.42*t,q*(.405-.09*t),(1.130-.065*q*q)*(1-t)+(.875-.020*q*q)*t)
h.panel('Curved bubble windshield',wind,22,26,glass);h.panel('Dark curved canopy roof dome',roof,20,22,carbon);h.panel('Canopy aft engine glazing',aft,18,20,glass);h.line('Canopy windshield base seal',[wind(0,i/32)for i in range(33)],.009,carbon,7);h.line('Fine front roof header',[wind(1,i/32)for i in range(33)],.007,carbon,7)
for name,s in [('Left',1),('Right',-1)]:
 h.CURRENT=doors[name]
 def upper(t):return Vector(wind(t/.56,0 if s<0 else 1))if t<.56 else Vector(roof((t-.56)/.44,0 if s<0 else 1))
 def side(t,u):
  a=Vector((.79-2.01*t,s*(.595+.040*math.sin(math.pi*t)),.738+.105*t+.015*math.sin(math.pi*t)));p=a*(1-u)+upper(t)*u;p.y+=s*.020*math.sin(math.pi*u)*math.sin(math.pi*t);return p
 h.panel('Separate curved canopy door glass '+name,side,28,12,glass,normal_hint=(0,s,.2))
 for u in(0,1):h.line('Canopy door perimeter seal '+name,[side(i/32,u)for i in range(33)],.009,carbon,7)
 h.line('Canopy door rear diagonal seal '+name,[side(1,i/16)for i in range(17)],.009,carbon,7);h.panel('Green canopy lower door belt '+name,lambda t,u:(lambda p:(p[0],p[1]+s*.025*u,p[2]-.055*u))(side(t,0)),24,6,paint,normal_hint=(0,s,.6));h.box('Flush canopy release '+name,(-.53,s*.658,.785),(.095,.013,.021),carbon,.008)
 h.line('Airfoil mirror stalk '+name,[(.30,s*.68,.84),(.32,s*.99,.91)],.011,carbon,7);pod=h.box('Compact canopy mirror pod '+name,(.33,s*1.055,.925),(.20,.13,.075),carbon,.028);pod.rotation_euler.z=s*.16;h.box('Canopy mirror glass '+name,(.228,s*1.055,.927),(.006,.10,.05),glass,.014)
h.CURRENT=body
for s in(-1,1):
 def sail(t,u,sg=s):
  a=Vector((-1.01-.21*t,sg*(.405+.190*t),1.065-.222*t));b=Vector((-1.43,sg*.315,.855));return a*(1-u)+b*u
 h.panel('Organic filled rear canopy sail',sail,14,12,paint,normal_hint=(0,s,.6))
h.line('Compact windshield wiper',[wind(.045,.26),wind(.09,.70)],.0045,carbon,6);h.cockpit(paint,carbon,glass,alloy,interior,white)
# Rear cooling channels and an original restrained powertrain-cover impression.
for s in(-1,1):
 h.panel('Rear deck tapered dark channel',lambda t,u,sg=s:(-1.35-.62*t,sg*(.40+.19*u),top(-1.35-.62*t,sg*(.40+.19*u))+.011),18,8,carbon)
 for j in range(7):x=-1.40-j*.076;h.line('Rear deck diagonal cooling slat',[(x,s*.41,top(x,s*.41)+.021),(x-.04,s*.57,top(x-.04,s*.57)+.021)],.007,alloy,6)
 h.box('Fictional compact powertrain cover',(-1.61,s*.17,.76),(.48,.20,.12),carbon,.035);h.line('Raised green deck spine edge',[(-1.28,s*.37,.90),(-1.65,s*.36,.84),(-1.99,s*.34,.77)],.012,paint,7)
h.box('Canopy slim roof intake',(-.90,0,1.153),(.28,.22,.065),carbon,.030);h.box('Roof intake dark mouth',(-.746,0,1.155),(.01,.16,.035),carbon,.012)
def rx(y):return sweep(-2.37,y)-.014
h.panel('Recessed curved rear fascia',lambda t,u:(rx((t*2-1)*.82),(t*2-1)*.82,.38+u*.25),28,8,carbon,normal_hint=(-1,0,0));h.line('Thin continuous original red rear light',[(rx(y)-.012,y,.65+.035*(abs(y)/.80)**1.5)for y in[-.80+1.60*i/44 for i in range(45)]],.009,red,8)
for s in(-1,1):
 h.cylinder('Recessed boost outlet dark back',(-2.317,s*.56,.255),.072,.016,carbon,'X',32);h.torus('Machined rear boost outlet lip',(-2.40,s*.56,.255),.076,.0065,alloy,'X',32,6);vv=[(x,s*.56+.072*math.cos(2*math.pi*j/32),.255+.072*math.sin(2*math.pi*j/32))for x in(-2.40,-2.325)for j in range(32)];ff=[(j,j+32,(j+1)%32+32,(j+1)%32)for j in range(32)];h.mesh('Open cylindrical boost tube wall',vv,ff,carbon,True);h.line('Rear diffuser outer lip',[(-2.40,s*.90,.18),(-2.16,s*.91,.14),(-1.96,s*.86,.17)],.020,carbon,8)
for y in(-.66,-.44,-.22,0,.22,.44,.66):h.mesh('Deep rear carbon diffuser fin',[(-2.40,y,.13),(-1.95,y,.13),(-2.02,y,.34),(-2.38,y,.35)],[(0,1,2,3)],carbon,False,normal_hint=(0,1,0))
for j in range(24):y=-.74+j*1.48/23;h.line('Fine dark rear radiator web',[(rx(y)-.005,y,.42),(rx(y)-.005,y,.60)],.0016,carbon,4)
h.CURRENT=wing
for s in(-1,1):h.box('Fixed low rear wing support',(-2.02,s*.56,.875),(.13,.035,.22),carbon,.010)
p=h.panel('Separate curved rear aero wing',lambda t,u:(-2.20+.30*t+.08*(u*2-1)**2,(u*2-1)*.95,.992+.020*math.sin(math.pi*t)-.018*(u*2-1)**2),8,16,carbon);so=p.modifiers.new('Composite wing actual thickness','SOLIDIFY');so.thickness=.012
for s in(-1,1):h.line('Rear wing slim green end cap',[(-2.12,s*.95,.970),(-1.82,s*.95,.970)],.017,paint,8)
w=h.build_wheels(root,groups,paint,alloy,rubber,prefix='Verdant',lateral=.924,spokes=7);h.CURRENT=None;bpy.context.view_layer.update();root['vehicle']='Reconstructed Verdant Canopy GT';root['provenance']='New original geometry rebuilt after source loss, not previous V12 bytes.'
native=OUT/'verdant.blend';bpy.ops.wm.save_as_mainfile(filepath=str(native));m={'asset':'Verdant Canopy GT','vehicle_id':'verdant','reconstruction':True,'coordinates':'metres; +X forward,+Y up,-Z left','car_root':'CAR_ROOT','body_mesh':'CarBody','paint_material':paint.name,'glass_material':glass.name,'wheelbase_m':2.7,'wheel_radius_m':.366,'wheel_centers_three':{k:[o.location.x,o.location.z,-o.location.y]for k,o in w['steers'].items()},'steer_nodes':['Steer_'+k for k in w['steers']],'spin_nodes':['Spin_'+k for k in w['steers']],'steer_axis':'Three local +Y','spin_axis_for_forward':'Three local -Z','max_visual_steer_rad':None,'chassis_pose_limits':{'roll_rad':.008,'pitch_rad':.005,'heave_m':.002},'boost_mounts_three_m':[[-2.4,.255,-.56],[-2.4,.255,.56]],'wing_type':'Fixed RearWing, not AeroWing_Hinge','doors':'Separate fixed closed glazed panels; no opening mechanism supplied.','source':'assets/cars/verdant/verdant.blend','source_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'generator':'blender/build_verdant.py','rights':'No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses.','provenance':'Original reconstructed geometry/materials. User photograph and prior preview inform silhouette only; no logos/photo textures embedded. Not licensed CAD or exact prior source recovery.','status':'Generated; visual and exported-geometry QA pending.'};m=h.export_glb(groups,WEB/'car_verdant.glb',m)
for p in(OUT/'manifest.json',WEB/'car_verdant_manifest.json'):p.write_text(json.dumps(m,indent=2))
shutil.copy2(WEB/'car_verdant.glb',PUBLIC/'car_verdant.glb');print('VERDANT_REBUILT',json.dumps(m),flush=True)
