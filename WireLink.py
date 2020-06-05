

bl_info = {
    "name" : "WireLink",
    "Author" : "Vibhor Gupta",
    "version" : (1, 0),
    "blender" : (2, 82, 0),
    "location" : "View3D > Tool"

}

import bpy
import mathutils
import random


class WireLink_OT(bpy.types.Operator):
    
    bl_idname = "object.wire_link"
    bl_label = "WireLink"
    bl_options = {'REGISTER','UNDO'}
        
    #initializing inputs 
    num_h: bpy.props.IntProperty(name = 'Number of Wires', default = 6, min = 0,  max = 50)
    subd: bpy.props.IntProperty(name = "Number of Handles ", default = 2, min =2, max = 8)
    emitrad: bpy.props.FloatProperty(name = 'Overall Thickness', default = 0.2, min = 0.2, max = 2, precision = 2) 
    dmin: bpy.props.IntProperty(default = 3, min = 0)
    dmax: bpy.props.IntProperty(default = 10, max = 100)
    even: bpy.props.BoolProperty(name = 'Even Thickness', default = False)
    bdepth: bpy.props.FloatProperty(name = "Wire Thickness", default = 0.05,  min = 0.05, max = 5.00, precision = 2)
    
     
     
     
    
    
#    def invoke(self, context, event):
#        wm = context.window_manager
#        return wm.invoke_props_dialog(self)


    def execute(self,context):
        
        #original script 
        ############################### 

        #getting info on selected objects and selecting
        def CreateTube(v1,v2,splist = []):
            #n = number cuts, bdep = 
            #creating spline between two given vertex locations 
            mid = (v1+v2)/2
            
            #Adding the curve and deleting the current vertices
            bpy.ops.curve.primitive_bezier_curve_add(enter_editmode = True, location = mid)   
            bpy.ops.curve.select_all(action='SELECT')
            bpy.ops.curve.delete(type='VERT')
            
            #adding spline points at given locations
            bpy.ops.curve.vertex_add(location = v1)
            bpy.ops.curve.vertex_add(location = v2)
            bpy.ops.curve.handle_type_set(type = 'AUTOMATIC')
             
            if self.dmin == self.dmax:
                self.dmin = self.dmax - 1
            if self.even == True:
                bdepth = self.bdepth
            else:
                bdepth = (random.randrange(self.dmin, self.dmax))/100
            subd = self.subd
            #currently in editmode
            bpy.ops.curve.select_all(action='SELECT')
            bpy.ops.curve.subdivide(number_cuts = subd)
            bpy.context.object.data.bevel_depth = bdepth 
            bpy.ops.object.editmode_toggle()
            splist.append(bpy.context.active_object)

        #function to rotate one object towards another object 
        #object must have face 
        def Turn(o1,o2):
            vec = o1.location - o2.location 
            for i in (o1,o2):
                norm = i.data.polygons[0].normal
                rotdiff = norm.rotation_difference(vec) 
                i.rotation_mode = 'QUATERNION'
                i.rotation_quaternion = rotdiff
                
        #getting the global vector location(v) WRT object(o)        
        def WorldLoc(o,v):
            gco = mathutils.Vector()
            gco = o.location + v
            return gco 

        #adding two planes at the given locations with particle systems 
        def Emit_Add(oblist):
            emitlist = []
            
            for i in oblist:
                bpy.ops.mesh.primitive_circle_add(radius = self.emitrad,enter_editmode = True, location = i.location)
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.edge_face_add()
                bpy.ops.object.editmode_toggle()
                emitlist.append(bpy.context.active_object)
                
            print('EMITTERS, DONE')
            return(emitlist)
                
        #apply and copy particle systems from active to selected                 
        #creates particle system on one object and duplicates it on all other objects 
        def Generate_Points(oblist):
            oblist[0].select_set(True)
            view_layer = bpy.context.view_layer
            view_layer.objects.active = oblist[0]
            
            #particle systems on the first object
            bpy.ops.object.particle_system_add()
            ps = oblist[0].particle_systems
            ps[0].settings.count = self.num_h
            
            #particle frame scene to current scene frame 
            scene = bpy.data.scenes
            frame = scene[0].frame_current
            ps[0].settings.frame_start = frame
            ps[0].settings.frame_end = frame
            ps[0].settings.physics_type = 'NO'
            
            #copying particle_systems settings on the second object
            oblist[1].select_set(True)
            bpy.ops.particle.copy_particle_systems()
           
        #to get particle location of the added particle system   
        def GetParticle_Location(obj):
            ploc = []
            depg = bpy.context.evaluated_depsgraph_get()
            depob = obj.evaluated_get(depg)
            ps = depob.particle_systems[0]
            
            #loop to run through each particle and get its location 
            for p in ps.particles:
                local_co = p.location
                ploc.append(local_co)
            return ploc

        #To stich the Endpoints with the Empty
        def Stitch_Ends(spl_list, oblist):
            bpy.ops.object.select_all(action='DESELECT')
            view_layer = bpy.context.view_layer

            for i in range(len(oblist)):
                ob = oblist[i]
                ob.select_set(True)

                for sp in spl_list:
                    sp.select_set(True)
                    view_layer.objects.active = sp
                    
                    if bpy.ops.object.editmode_toggle.poll():
                        bpy.ops.object.editmode_toggle()    
                    bpy.ops.curve.select_all(action='DESELECT')
                    spline = sp.data.splines[0]
                    bp = spline.bezier_points
                    if i == 0:
                        bp[0].select_control_point = True
                    else:
                        bp[-1].select_control_point = True
                        
                    bpy.ops.object.hook_add_selob(use_bone=False)
                    bpy.ops.curve.select_all(action = 'DESELECT')
                    bpy.ops.object.editmode_toggle()
                    sp.select_set(False)

                ob.select_set(False)

        #to add handle to the given spline list
        def Handle_Add(splist):
            pointlist =  splist[0].data.splines[0].bezier_points
            pcount = len(pointlist)
            medianp = []
            Hlist = []
            
            # set all the splines to edit mode 
            for i in splist:
                i.select_set(True)
            bpy.ops.object.editmode_toggle()
            
            #loop from 1 to end-1: selecting the median points of the BezierPoints
            bpy.context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
            for i in range(1, pcount-1):
                avgp = []
                #this loop fills in the list with nth points of all splines 
                for j in splist:
                    p = j.data.splines[0].bezier_points[i]
                    #getting the world coordinates 
                    mat = j.matrix_world
                    local_co = p.co
                    world_co = mat@local_co
                    avgp.append(world_co)
                    
                
                #getting the median from the avgp list
                n = len(avgp)
                med = sum(avgp , mathutils.Vector()) /n
                medianp.append(med)
                bpy.ops.object.editmode_toggle()
            
            #initializing for rotating the created handle 
            lm = len(medianp)
            dirvec = medianp[lm -1] - medianp[0]
            
            #creating the handles at median points and rotating them 
            for m in medianp:
                
                bpy.ops.mesh.primitive_circle_add(location = m, radius = self.emitrad + 0.5)
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all(action='SELECT') 
                bpy.ops.mesh.edge_face_add()
                bpy.ops.object.editmode_toggle()
                bpy.context.object.display_type = 'WIRE'
                bpy.context.object.hide_render = True
                
                #turning the handle so that the handle is perpendicular to the wires
                hand = bpy.context.active_object 
                norm = hand.data.polygons[0].normal
                rotdiff = norm.rotation_difference(dirvec)
                hand.rotation_mode = 'QUATERNION'
                hand.rotation_quaternion = rotdiff
                
                #naming, storing and returning the added  handle list the handle list
                #hand.name = f'Handle { medianp.index(m) }'  
                Hlist.append(bpy.context.active_object)
            #print('CREATED HANDLES',Hlist)
            return Hlist
             
        #to attach the handles to the bezier points
        def Attach_Handle(spline_list, handle_list):
            temp_splist = spline_list.copy()
            temp_hlist = handle_list .copy()
            view_layer = bpy.context.view_layer
            bpy.ops.object.select_all(action='DESELECT')
            
            Hlen = len(temp_hlist)
            
            for i in range(Hlen):
                
                H = handle_list[i]
                H.select_set(True)
                #print('selected handle :', H.name)
                
                for S in temp_splist:
                    S.select_set(True)
                    view_layer.objects.active = S
                    bpy.ops.object.mode_set(mode = 'EDIT')
                    
                    bpy.ops.curve.select_all(action='DESELECT')
                    
                    #Selected the object and the spline to be attached 
                    #Now get the bezier points to be attached sequentially 
                    
                    bezpoint = S.data.splines[0].bezier_points
                    #print('working on {}st spline'.format(i))
                    
                    bezpoint[i+1].select_control_point = True
                    #Attach the selected point with the selected handle 
                    bpy.ops.object.hook_add_selob(use_bone = False)
                    bpy.ops.curve.select_all(action='DESELECT')
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                    S.select_set(False)
                    
                    #returned to the object mode and deselected the previous spline 
                    #print('STICHED handle to splines')
                    
                H.select_set(False) 

        def OB_join(olist):
            bpy.ops.object.select_all(action = 'DESELECT')
            for x in olist:
                x.select_set(True)
            view_layer = bpy.context.view_layer
            view_layer.objects.active = olist[0]
            bpy.ops.object.join()
            
        def Mat_Apply(olist):
            view_layer = bpy.context.view_layer
            bpy.ops.object.select_all(action = 'DESELECT')
            for x in olist:
                x.select_set (True)
            view_layer.objects.active = olist[0]
            
            bpy.ops.material.new()
            bpy.data.materials['Material']
            Color_material = bpy.data.materials["Material"]
            
            bpy.ops.object.make_links_data(type='MATERIAL')
            
            active = bpy.context.active_object
            active.active_material = Color_material
            active.data.materials[0].name = 'Wires'


        

        #Main program 
        
        obj = bpy.context.selected_objects
#        if len(obj) == 0: 
#            self.report({'ERROR'},'an error occurred')
        
        try:
            if len(obj) >= 2:
                spl_list = []

                Emitters = Emit_Add(obj)
                print(Emitters)
                Turn(Emitters[0], Emitters[1])

                Generate_Points(Emitters)

                loclist1 = GetParticle_Location(Emitters[0])
                loclist2 = GetParticle_Location(Emitters[1])
                
                l = len(loclist1)

                for x in range(l):
                    p1 = loclist1[x]
                    p2 = loclist2[x]
                    CreateTube(p1, p2, spl_list)

                Handle_list = Handle_Add(spl_list)
                Attach_Handle(spl_list, Handle_list)
                Stitch_Ends(spl_list, obj)
                
                        

                for x in Emitters:
                    x.select_set(True)
                    bpy.ops.object.delete()
                    
                Mat_Apply(spl_list)

                # OB_join(spl_list)
            else:
                self.report({'ERROR'},'2 points must be selected')

        except:
            self.report({'ERROR'}, 'start and endpoint not selected')

        

        return {'FINISHED'} 
        ###############################       

class WireLink_PT(bpy.types.Panel):
    bl_idname = "object.wire_link_pt"
    bl_label = "WireLink"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "WLink"
    
    
    @classmethod 
    def poll(cls, context):
        return context.object 

    def draw(self, context):
        layout = self.layout
        
        row = layout.row()
#        row.operator(text = 'Create', operator = 'object.wire_link')
        props = layout.operator(text = 'Create Link', operator = 'object.wire_link')
        
def register():
    bpy.utils.register_class(WireLink_OT)
    bpy.utils.register_class(WireLink_PT)
    
def unregister():
    bpy.utils.unregister_class(WireLink_OT)
    bpy.utils.unregister_class(WireLink_PT)

if __name__=="__main__":
    register()
