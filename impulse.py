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
    o.keyframe_insert('rotation')
    
def set_quality(self, context):
    frame_rate = context.scene.render.fps
    q = context.scene.impulse_props.quality
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


class ImpulseSetInitial(bpy.types.Operator):
    bl_idname = "rigidbody.impulse_set_initial"
    bl_label = "Set Initial Position"  
    bl_description = "Set the object's initial position and rotation to the current location and rotation"
    
    @classmethod
    def poll(cls, context):
        if context.active_object:
            return context.active_object.type == 'MESH'
    
    def execute(self, context):
        context.scene.impulse_props.s = context.active_object.location
        context.scene.impulse_props.r = context.active_object.rotation_euler
        return {'FINISHED'}

    
class ImpulseInitializeVelocity(bpy.types.Operator):
    bl_idname = "rigidbody.impulse_initialize_velocity"
    bl_label = "Initialize Velocity"
    
    @classmethod
    def poll(cls, context):
        if context.active_object:
            return context.active_object.type == 'MESH'

    def execute(self, context):
        props = context.scene.impulse_props
        
        object = bpy.context.active_object
        
        frame_rate = bpy.context.scene.render.fps

        # Make sure it is a rigid body
        if object.rigid_body is None:
            bpy.ops.rigidbody.objects_add()
        
        # Animate it!
        object.animation_data_clear()
        
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
        object.keyframe_insert(data_path='location')
        object.keyframe_insert(data_path='rotation_euler')
        
        bpy.context.scene.frame_current += 1
        
        # Set end keyframe
        object.location = new_loc
        object.rotation_euler = new_rot
        object.keyframe_insert(data_path='location')
        object.keyframe_insert(data_path='rotation_euler')
        
        # Set animated checkbox
        object.rigid_body.kinematic = True
        object.keyframe_insert('rigid_body.kinematic')
        
        bpy.context.scene.frame_current += 1
        
        # Set unanimated checkbox
        object.rigid_body.kinematic = False
        object.keyframe_insert('rigid_body.kinematic')
        
        bpy.context.scene.frame_current = 0
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
        
        props = context.scene.impulse_props
        
        row = layout.row()
        column = row.column()
        column.prop(props, 's')
        column.prop(props, 'r')
        column.operator("rigidbody.impulse_set_initial")
        
        column = row.column()
        column.prop(props, 'v')
        #column.prop(props, 'total_v')
        total_v = math.sqrt(pow(props.v.x, 2) + pow(props.v.y, 2) + pow(props.v.z, 2))
        label = "Total Velocity: " + "{:10.4f}".format(total_v)
        column.label(text=label)
        column.prop(props, 'av')
        
        row = layout.row()
        row.separator()
        row = layout.row()
        row.label(text="Quality:")
        row.prop(props, 'quality', expand=True)
        
        row = layout.row()
        row.prop(props, 'start_frame')
        
        layout.row().operator("rigidbody.impulse_initialize_velocity")


# Addon Properties
class ImpulseProperties(bpy.types.PropertyGroup):
    start_frame = bpy.props.IntProperty(
        name="Start Frame",
        description="Frame to start velocity initialization on",
        default=1,
        min=bpy.context.scene.frame_start,
        max = bpy.context.scene.frame_end)
        
    s = bpy.props.FloatVectorProperty(
        name="Initial Position",
        description="Initial position for the object",
        subtype='TRANSLATION')
    
    r = bpy.props.FloatVectorProperty(
        name="Initial Rotation",
        description="Initial rotation for the object",
        subtype='EULER')
        
    v = bpy.props.FloatVectorProperty(
        name="Velocity",
        description="Axis-dependent velocity",
        subtype='VELOCITY',
        update=update_total_v)
        
    av = bpy.props.FloatVectorProperty(
        name="Angular Velocity",
        description="Axis-dependent angular velocity",
        subtype='EULER')
        
    total_v = bpy.props.FloatProperty(
        name="Total Velocity",
        description="Total velocity",
        unit='VELOCITY')
        
    quality = bpy.props.EnumProperty(
        name="Quality",
        items=[("low", "Low", "Use low quality settings"),
               ("medium", "Medium", "Use medium quality settings"),
               ("high", "High", "Use high quality settings")],
        default='high',
        update=set_quality)



def register():
    bpy.utils.register_module(__name__)
    
    bpy.types.Scene.impulse_props = bpy.props.PointerProperty(type=ImpulseProperties)


def unregister():
    bpy.utils.unregister_module(__name__)
    
    del bpy.types.Scene.init_vel_props


if __name__ == "__main__":
    register()
