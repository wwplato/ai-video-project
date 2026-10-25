"""Closed architectural shell and detailed premium sliding glazing."""
import bpy,math
from mathutils import Vector

def enclose_room(w):
 from scene import cube,mat,cyl
 # The cameras are inside this complete shell, including the previous missing
 # right return and lintel. Only the real window opening exposes the panorama.
 wall=bpy.data.objects.get('Architectural plaster wall');wall.location=(-3.43,-2.25,1.92);wall.dimensions=(.22,9.1,3.84)
 floor=bpy.data.objects.get('Oak floor');floor.location=(.65,-2.1,-.09);floor.dimensions=(8.6,9.6,.18)
 cube('Right interior wall',(4.72,-2.25,1.92),(.22,9.1,3.84),w.ivory,.016)
 cube('Rear interior wall',(.65,-6.76,1.92),(8.35,.22,3.84),w.ivory,.016)
 cube('Window wall right return',(3.83,2.24,1.92),(1.80,.22,3.84),w.ivory,.014)
 cube('Window wall left return',(-3.43,2.24,1.92),(.24,.22,3.84),w.ivory,.014)
 cube('Solid lintel above glazing',(-.2,2.24,3.68),(6.35,.25,.40),w.ivory,.014)
 cube('Interior ceiling',(.65,-2.24,3.87),(8.4,9.35,.14),w.ivory,.016)
 stone=mat('Honed warm travertine',(.42,.38,.30),.6)
 cube('Deep travertine window sill',(-.2,1.99,.09),(6.5,.58,.18),stone,.025)
 for x in [-3.30,4.59]:cube('Solid wall skirting',(x,-2.25,.09),(.025,8.9,.16),stone,.004)
 cube('Window wall skirting',(3.82,2.10,.09),(1.69,.03,.16),stone,.004)
 # Quiet architectural details make the wall clearly readable as an interior.
 for x in [3.22,3.52,3.82,4.12,4.42]:cube('Walnut wall fluting',(x,2.107,1.79),(.065,.035,3.32),w.oak,.010)
 warm=mat('Warm cove diffuser',(.8,.72,.52),.5);bs=warm.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=(1,.70,.34,1);bs.inputs['Emission Strength'].default_value=.65
 cube('Warm ceiling cove',(-.20,1.96,3.61),(6.5,.035,.022),warm,.006)
 cube('Right return cove',(3.02,2.07,1.91),(.018,.03,3.35),warm,.004)

def upgrade_window(w):
 from scene import cube,mat,cyl
 frame=mat('Satin champagne anodized aluminium',(.34,.255,.155),.29,.83)
 # Directional micrograin keeps the hardware detailed without coarse noise.
 ns=frame.node_tree.nodes;ls=frame.node_tree.links;tex=ns.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=350;tex.inputs['Detail'].default_value=2;bump=ns.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.07;bump.inputs['Distance'].default_value=.00013;ls.new(tex.outputs['Fac'],bump.inputs['Height']);ls.new(bump.outputs['Normal'],ns.get('Principled BSDF').inputs['Normal'])
 anisotropy=ns.get('Principled BSDF').inputs.get('Anisotropic')
 if anisotropy is not None:anisotropy.default_value=.38
 rubber=mat('EPDM graphite glazing seal',(.009,.013,.014),.89)
 edge=mat('Low E laminated glass edge',(.075,.22,.20),.22,.35)
 shadow=mat('Thermal break profile',(.028,.038,.040),.48,.55)
 for ob in list(bpy.data.objects):
  if ob.name.startswith('Outer titanium jamb'):
   ob.dimensions=(.145,.235,3.42);ob.data.materials.clear();ob.data.materials.append(shadow)
  elif ob.name.startswith('Double sliding track'):
   ob.dimensions=(6.30,.25,.105);ob.data.materials.clear();ob.data.materials.append(shadow)
 for k,root in enumerate(w.pane_roots):
  shift=-.085 if k else 0;x0,x1=(-3.24,-.20) if k==0 else (-.20,2.84);y=(2.04 if k==0 else 1.9)
  for ob in list(root.children):
   ob.location.y+=shift
   if ob.name.startswith('Sash vertical'):
    ob.dimensions=(.078,.125,3.27);ob.data.materials.clear();ob.data.materials.append(frame)
   elif ob.name.startswith('Sash horizontal'):
    ob.dimensions=(x1-x0,.125,.075);ob.data.materials.clear();ob.data.materials.append(frame)
   elif ob.name.startswith('Handle') or ob.name.startswith('Sliding window grip'):bpy.data.objects.remove(ob,do_unlink=True)
  def part(ob):ob.parent=root;return ob
  for x in [x0+.050,x1-.050]:
   part(cube('Continuous vertical glazing gasket',(x,y-.012,1.80),(.011,.018,3.12),rubber,.003))
   part(cube('Polished laminated vertical glass edge',(x+.012 if x<x0+.1 else x-.012,y-.018,1.80),(.006,.014,3.11),edge,.002))
  for z in [.230,3.369]:
   part(cube('Continuous horizontal glazing gasket',((x0+x1)/2,y-.012,z),(x1-x0-.10,.018,.010),rubber,.003))
   part(cube('Thermal break joint',((x0+x1)/2,y+.042,z),(x1-x0-.11,.014,.008),shadow,.002))
  # Visible spacer and a second, very lightly tinted glazing surface.
  glass=next(ob for ob in root.children if ob.name.startswith('Actual glass sheet'))
  copy=glass.copy();copy.data=glass.data.copy();bpy.context.collection.objects.link(copy);copy.name='Second low E glass laminate';copy.location.y+=.023;copy.parent=root
  if k:
   x=x1-.132
   part(cube('Recessed handle pocket',(x,y-.073,1.575),(.115,.026,.410),shadow,.025))
   part(cube('Flush handle escutcheon',(x,y-.092,1.575),(.081,.031,.354),frame,.020))
   part(cube('Handle finger clearance',(x-.018,y-.114,1.575),(.037,.016,.246),rubber,.015))
   part(cube('Sculpted floating handle',(x+.012,y-.135,1.575),(.027,.048,.270),frame,.012))
   for z in [1.45,1.70]:part(cube('Handle return',(x+.012,y-.114,z),(.027,.065,.025),frame,.009))
   bpy.ops.object.text_add(location=(x-.028,y-.112,1.718),rotation=(math.pi/2,0,0));mark=bpy.context.object;mark.name='Handle engraved LUMINEX';mark.data.body='LUMINEX';mark.data.size=.012;mark.data.extrude=.0002;mark.data.materials.append(rubber);mark.parent=root
   # Engraved-looking physical wordmark in the lower aluminium profile.
   bpy.ops.object.text_add(location=(x1-.65,y-.065,.17),rotation=(math.pi/2,0,0));label=bpy.context.object;label.name='LUMINEX hardware wordmark';label.data.body='LUMINEX';label.data.size=.050;label.data.extrude=.0005;label.data.space_character=1.25;label.data.materials.append(rubber);label.parent=root
 for yy in [1.90,2.04]:
  cube('Recessed bottom guide',(-.2,yy,.137),(6.17,.023,.017),rubber,.004)
  cube('Polished track bearing',(-.2,yy-.019,.149),(6.17,.009,.007),frame,.003)
 for x in [-2.8,-1.55,-.30,.95,2.2]:cube('Sill drainage slot',(x,1.82,.182),(.055,.015,.005),rubber,.003)
 cube('Integrated AI sensor housing',(-.2,1.91,3.43),(.34,.12,.075),frame,.022)
 for x in [-.285,-.20,-.115]:
  o=cyl('Recessed optical sensor',(x,1.843,3.435),.011,.012,rubber);o.rotation_euler.x=math.pi/2
 led=bpy.data.materials.new('Window state light');led.use_nodes=True;n=led.node_tree.nodes;n.clear();w.state_light_shader=n.new('ShaderNodeEmission');w.state_light_shader.inputs['Color'].default_value=(.38,.80,.70,1);w.state_light_shader.inputs['Strength'].default_value=.8;out=n.new('ShaderNodeOutputMaterial');led.node_tree.links.new(w.state_light_shader.outputs[0],out.inputs['Surface'])
 cube('Integrated status light',(-.2,1.84,3.41),(.18,.005,.006),led,.002)
 w.glass_panes=[next(ob for ob in root.children if ob.name.startswith('Actual glass sheet')) for root in w.pane_roots]
