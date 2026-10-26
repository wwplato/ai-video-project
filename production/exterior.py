"""A physical coastal terrace and matching exterior facade around LUMINEX."""
import bpy,math,random
from mathutils import Vector

def build_exterior(w):
 from scene import cube,mat,cyl,sphere,textured,ASSET
 before=set(bpy.data.objects);w.panorama.location=(-.3,32,2.6);w.panorama.scale=(31,17.5,1)
 stone=mat('Exterior honed limestone',(.53,.48,.39),.73);ns=stone.node_tree.nodes;ls=stone.node_tree.links;noise=ns.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95;noise.inputs['Detail'].default_value=3;bump=ns.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.002;ls.new(noise.outputs['Fac'],bump.inputs['Height']);ls.new(bump.outputs[0],ns.get('Principled BSDF').inputs['Normal'])
 w.exterior_stone=stone; joint=mat('Exterior stone joints',(.17,.16,.14),.85);metal=mat('Terrace brushed bronze',(.27,.23,.17),.27,.82)
 cube('Coastal terrace slab',(.5,3.86,-.135),(8.4,3.65,.27),stone,.035)
 for x in range(12):cube('Terrace stone joint',(-3.65+x*.74,3.87,.003),(.007,3.5,.004),joint,.001)
 for y in [2.55,3.35,4.15,4.95]:cube('Terrace transverse joint',(.5,y,.004),(8.25,.007,.004),joint,.001)
 cube('Exterior facade left stone pier',(-3.65,2.48,1.78),(.53,.43,3.83),stone,.018)
 cube('Exterior facade right stone pier',(3.83,2.48,1.78),(1.80,.43,3.83),stone,.018)
 cube('Exterior facade limestone lintel',(-.2,2.48,3.65),(7.45,.45,.42),stone,.018)
 cube('Exterior sill reveal',(-.2,2.44,.045),(6.35,.82,.09),stone,.015)
 cube('Upper balcony overhang',(.5,3.25,3.89),(8.4,2.45,.24),stone,.025)
 for x in [3.14,3.36,3.58,3.80,4.02,4.24]:cube('Exterior bronze facade fin',(x,2.76,1.76),(.055,.33,3.48),metal,.009)
 rail_glass=bpy.data.materials.new('Terrace low iron safety glazing');rail_glass.use_nodes=True;n=rail_glass.node_tree.nodes;n.clear();t=n.new('ShaderNodeBsdfTransparent');t.inputs[0].default_value=(.90,.97,.98,1);g=n.new('ShaderNodeBsdfGlossy');g.inputs['Color'].default_value=(.63,.77,.80,1);g.inputs['Roughness'].default_value=.04;m=n.new('ShaderNodeMixShader');m.inputs[0].default_value=.035;o=n.new('ShaderNodeOutputMaterial');l=rail_glass.node_tree.links;l.new(t.outputs[0],m.inputs[1]);l.new(g.outputs[0],m.inputs[2]);l.new(m.outputs[0],o.inputs[0])
 cube('Terrace safety rail base',(.5,5.58,.12),(8.4,.20,.24),stone,.018)
 for j in range(6):
  x=-3.0+j*1.4;cube('Terrace laminated guard panel',(x,5.57,.79),(1.34,.014,1.04),rail_glass,.004)
  cube('Terrace bronze rail post',(x-.69,5.57,.75),(.035,.045,1.25),metal,.005)
 cube('Terrace continuous handrail',(.5,5.57,1.33),(8.4,.055,.038),metal,.008)
 planter=mat('Sandstone outdoor planter',(.38,.36,.30),.79);soil=mat('Exterior planting soil',(.055,.047,.03),.99);leaf=mat('Coastal olive foliage',(.12,.22,.09),.65);wood=mat('Olive tree bark',(.19,.14,.08),.86);w.exterior_leaves=[];rng=random.Random(2035)
 for x,y,size in [(-3.18,4.73,.8),(3.78,4.81,1.0)]:
  cube('Terrace planted trough',(x,y,.29),(.68*size,.72*size,.58),planter,.045);cube('Terrace dark soil',(x,y,.586),(.58*size,.61*size,.022),soil,.01)
  for b in range(4):
   bx=x+rng.uniform(-.16,.16);by=y+rng.uniform(-.15,.15);h=rng.uniform(.55,.95)*size;cyl('Terrace olive branch',(bx,by,.59+h/2),.012,h,wood)
   for j in range(11):
    angle=j*2.399+b;z=.75+j*.055*size;r=.18+.055*math.sin(j);ob=sphere('Terrace wind foliage',(bx+math.cos(angle)*r,by+math.sin(angle)*r,z),(.07*size,.15*size,.018),leaf);ob.rotation_euler=(.25*math.cos(angle),.4*math.sin(angle),angle);w.exterior_leaves.append((ob,ob.rotation_euler.copy(),rng.random()*6.28))
 # A neighboring bay provides scale and depth in the exterior camera move.
 dark=mat('Neighbor blue architectural glass',(.055,.12,.16),.19,.6)
 for level in [-1,0,1,2]:
  z=level*3.85;cube('Neighbor projecting balcony',(5.18,3.35,z+.10),(1.50,2.5,.20),stone,.018);cube('Neighbor recessed glazing',(5.65,2.40,z+1.85),(.22,1.55,3.3),dark,.01)
 # The rear-facing city plate is only visible beside the building in the
 # exterior shot; the complete rear wall hides it from every interior camera.
 bpy.ops.mesh.primitive_plane_add(size=2,location=(0,-24,2.6),rotation=(math.pi/2,0,0));back=bpy.context.object;back.name='Exterior reverse coastal horizon';back.scale=(34,19,1);back.data.materials.append(textured('Exterior surrounding bay',ASSET/'city.png',True));back.visible_shadow=False
 bpy.ops.object.light_add(type='AREA',location=(-1,7.2,5.5));w.exterior_fill=bpy.context.object;w.exterior_fill.name='Soft coastal facade fill';w.exterior_fill.data.energy=450;w.exterior_fill.data.color=(1,.84,.65);w.exterior_fill.data.size=5;w.exterior_fill.visible_glossy=False;w.exterior_fill.visible_transmission=False;w.exterior_fill.visible_camera=False;w.exterior_fill.data.specular_factor=0
 from scene import aim
 aim(w.exterior_fill,(0,2.4,1.8))
 w.exterior_objects=list(set(bpy.data.objects)-before)
 for ob in w.exterior_objects:
  if ob.type in ['MESH','FONT']:ob.pass_index=1

def animate_exterior(w,t):
 weather=1 if w.i==11 else .68*max(0,min(1,(t-3.3)/1.5)) if w.i==10 else 0
 u=max(0,min(1,(t-1.4)/1.5));dark=1 if w.i in [3,9] or (w.i==1 and t>=5) else 1-u*u*(3-2*u) if w.i==4 else 0
 w.exterior_fill.data.energy=450*(1-dark)*(1-.9*weather)
 w.exterior_stone.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.73-.45*weather
 phase_t=weather*1.5 if w.i in [2,10,11] else t
 for ob,base,phase in w.exterior_leaves:
  ob.rotation_euler=(base.x+(.018+.16*weather)*math.sin(phase_t*(.8+weather)+phase),base.y+(.012+.10*weather)*math.cos(phase_t*1.1+phase),base.z)
