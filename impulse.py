bl_info = {
    "name": "Impulse",
    "author": "Nathan Craddock",
    "version": (1, 0),
    "blender": (2, 77, 0),
    "location": "Object Mode > Tool Shelf > Physics Tab",
    "description": "Set initial velocities for rigid body physics",
    "tracker_url": "",
    "category": "Object"
}

import bpy
from mathutils import Vector
import math

# Set keyframes
def set_keyframes(o):
    o.keyframe_insert('location')
    o.keyframe_insert('rotation_euler')
    
def set_quality(self, context):
    frame_rate = context.scene.render.fps
    q = context.scene.impulse_settings.quality
    if q == 'low':
        bpy.context.scene.rigidbody_world.steps_per_second = frame_rate * 2
    elif q == 'medium':
        bpy.context.scene.rigidbody_world.steps_per_second = frame_rate * 10
    elif q == 'high':
        bpy.context.scene.rigidbody_world.steps_per_second = frame_rate * 20
        
def update_total_v(self, context):
    props = context.scene.impulse_props
    total_v = math.sqrt(pow(props.v.x, 2) + pow(props.v.y, 2) + pow(props.v.z, 2))
    
    props.total_v = total_v
    
def update_individual_v(self, context):
    props = context.scene.impulse_props
    old_v = math.sqrt(pow(props.v.x, 2) + pow(props.v.y, 2) + pow(props.v.z, 2))
    
    if old_v != 0:
        props.v.x = (props.total_v * props.v.x) / old_v
        props.v.y = (props.total_v * props.v.y) / old_v
        props.v.z = (props.total_v * props.v.z) / old_v

class ImpulseAddObject(bpy.types.Operator):
    bl_idname = "rigidbody.impulse_add_object"
    bl_label = "Add Object"
    bl_description = "Add object to Impulse"
    
    @classmethod
    def poll(cls, context):
        if context.active_object:
            return context.active_object.type == 'MESH'
        
    def execute(self, context):
        if 'impulse_objects' not in bpy.data.groups:
            bpy.ops.group.create(name='impulse_objects')
        
        bpy.ops.object.group_link(group='impulse_objects')
        
        # Make sure it is a rigid body
        if context.active_object.rigid_body is None:
            bpy.ops.rigidbody.objects_add()
        
        return {'FINISHED'}
        

class ImpulseRemoveObject(bpy.types.Operator):
    bl_idname = "rigidbody.impulse_remove_object"
    bl_label = "Remove Object"
    bl_description = "Remove object from Impulse"
    
    @classmethod
    def poll(cls, context):
        if context.active_object:
            return context.active_object in list(bpy.data.groups['impulse_objects'].objects)
        
    def execute(self, context):
        bpy.ops.group.objects_remove(group="impulse_objects")
        
        # Remove animation data
        context.active_object.animation_data_clear()
        
        # HACKY! :D
        # Move frame forward, then back to update
        bpy.context.scene.frame_current += 1
        bpy.context.scene.frame_current -= 1
        
        # Make sure it animates...
        object.rigid_body.kinematic = False
        
        return {'FINISHED'}


class ImpulseSetLocation(bpy.types.Operator):
    bl_idname = "rigidbody.impulse_set_location"
    bl_label = "Use Current"  
    bl_description = "Use the current location"
    
    @classmethod
    def poll(cls, context):
        if context.active_object:
            return context.active_object.type == 'MESH'
    
    def execute(self, context):
        context.active_object.impulse_props.s = context.active_object.location
        return {'FINISHED'}
    
class ImpulseSetRotation(bpy.types.Operator):
    bl_idname = "rigidbody.impulse_set_rotation"
    bl_label = "Use Current"  
    bl_description = "Use the current rotation"
    
    @classmethod
    def poll(cls, context):
        if context.active_object:
            return context.active_object.type == 'MESH'
    
    def execute(self, context):
        context.active_object.impulse_props.r = context.active_object.rotation_euler
        return {'FINISHED'}

    
class ImpulseInitializeVelocity(bpy.types.Operator):
    bl_idname = "rigidbody.impulse_initialize_velocity"
    bl_label = "Initialize Velocity"
    
    @classmethod
    def poll(cls, context):
        if context.active_object:
            return context.active_object.type == 'MESH'

    def execute(self, context):
        object = bpy.context.active_object
        props = object.impulse_props
        frame_rate = bpy.context.scene.render.fps

        # Make sure it is a rigid body
        if object.rigid_body is None:
            bpy.ops.rigidbody.objects_add()
        
        # Animate it!
        object.animation_data_clear()
        
        if bpy.context.scene.frame_start > props.start_frame:
            props.start_frame = bpy.context.scene.frame_start
        
        bpy.context.scene.frame_current = props.start_frame
        
        displacement_x = props.v.x / frame_rate
        displacement_y = props.v.y / frame_rate
        displacement_z = props.v.z / frame_rate
        
        rdisplacement_x = props.av.x / frame_rate
        rdisplacement_y = props.av.y / frame_rate
        rdisplacement_z = props.av.z / frame_rate
        
        new_loc = Vector((props.s.x + displacement_x, props.s.y + displacement_y, props.s.z + displacement_z))
        new_rot = Vector((props.r.x + rdisplacement_x, props.r.y + rdisplacement_y, props.r.z + rdisplacement_z))
        
        # Set start keyframe
        object.location = props.s
        object.rotation_euler = props.r
        set_keyframes(object)
        
        bpy.context.scene.frame_current += 1
        
        # Set end keyframe
        object.location = new_loc
        object.rotation_euler = new_rot
        set_keyframes(object)
        
        # Set animated checkbox
        object.rigid_body.kinematic = True
        object.keyframe_insert('rigid_body.kinematic')
        
        bpy.context.scene.frame_current += 1
        
        # Set unanimated checkbox
        object.rigid_body.kinematic = False
        object.keyframe_insert('rigid_body.kinematic')
        
        bpy.context.scene.frame_current = 0
        
        settings = context.scene.impulse_settings
        
        if settings.auto_play and not bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()
            
        return {'FINISHED'}
    
    
class ImpulsePanel(bpy.types.Panel):
    bl_label = "Impulse"
    bl_idname = "impulse_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "objectmode"
    bl_category = "Physics"

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)        
        
        # If the group exists and has objects
        if 'impulse_objects' in bpy.data.groups:
            if context.active_object and context.active_object in list(bpy.data.groups['impulse_objects'].objects):
                props = context.object.impulse_props
                o = context.active_object.impulse_props
                
                row.operator('rigidbody.impulse_remove_object', icon='X')
                row = layout.row()
                column = row.column(align=True)
                column.prop(o, 's')
                column.operator("rigidbody.impulse_set_location", icon='MAN_TRANS')
                column.prop(o, 'r')
                column.operator("rigidbody.impulse_set_rotation", icon='MAN_ROT')
                
                column = row.column()
                column.prop(o, 'v')
                #column.prop(props, 'total_v')
                #total_v = math.sqrt(pow(props.v.x, 2) + pow(props.v.y, 2) + pow(props.v.z, 2))
                #label = "Total Velocity: " + "{:10.4f}".format(total_v)
                #column.label(text=label)
                column.prop(o, 'av')
                
                row = layout.row()
                row.separator()
                
                row = layout.row()
                row.prop(o, 'start_frame')
                
                
                layout.row().operator("rigidbody.impulse_initialize_velocity", icon='MOD_PHYSICS')
            else:
                row.operator('rigidbody.impulse_add_object', icon='ZOOMIN')
            
            # Addon settings
            settings = context.scene.impulse_settings
            
            layout.separator()
            box = layout.box()
            row = box.row()
            row.label(text="Quality:")
            row.prop(settings, 'quality', expand=True)
            row = box.row()
            #row.alignment = 'CENTER'
            row.prop(settings, 'auto_play')
            
        else:
            row.operator('rigidbody.impulse_add_object', icon='ZOOMIN')


# Addon Properties
class ImpulseObjectProperties(bpy.types.PropertyGroup):
    start_frame = bpy.props.IntProperty(
        name="Start Frame",
        description="Frame to start velocity initialization on",
        default=1)
        
    s = bpy.props.FloatVectorProperty(
        name="Location",
        description="Initial position for the object",
        subtype='TRANSLATION')
    
    r = bpy.props.FloatVectorProperty(
        name="Rotation",
        description="Initial rotation for the object",
        subtype='EULER')
        
    v = bpy.props.FloatVectorProperty(
        name="Velocity",
        description="Set the velocity of the object",
        subtype='VELOCITY',
        update=update_total_v)
        
    av = bpy.props.FloatVectorProperty(
        name="Angular Velocity",
        description="Set the angular velocity of the object",
        subtype='VELOCITY')

class ImpulseSettings(bpy.types.PropertyGroup):
    quality = bpy.props.EnumProperty(
        name="Quality",
        items=[("low", "Low", "Use low quality settings"),
               ("medium", "Medium", "Use medium quality settings"),
               ("high", "High", "Use high quality settings")],
        default='medium',
        update=set_quality)
        
    auto_play = bpy.props.BoolProperty(
        name="Auto Play",
        description="Automatically start the animation after running",
        default=False)

def register():
    bpy.utils.register_module(__name__)
    
    bpy.types.Object.impulse_props = bpy.props.PointerProperty(type=ImpulseObjectProperties)
    bpy.types.Scene.impulse_settings = bpy.props.PointerProperty(type=ImpulseSettings)


def unregister():
    bpy.utils.unregister_module(__name__)
    
    del bpy.types.Object.impulse_props
    del bpy.types.Scene.impulse_settings


if __name__ == "__main__":
    register()
