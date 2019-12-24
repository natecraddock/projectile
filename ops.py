# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy

from . import utils
from . import ui

class PHYSICS_OT_projectile_add(bpy.types.Operator):
    bl_idname = "rigidbody.projectile_add_object"
    bl_label = "Add Object as Projectile"
    bl_description = "Set selected object as a projectile"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == 'MESH' and not ob.projectile_props.is_projectile

    def set_instance_object(self, ob, instance):
        ob.projectile_props["instance_object"] = instance

    def execute(self, context):
        ob = context.object

        # Get parent instance collection
        projectile_collection = utils.get_projectile_collection()
        instances_collection = bpy.data.collections.new(f"instances_{ob.name}")

        projectile_collection.children.link(instances_collection)

        empty = bpy.data.objects.new(f"emitter_{ob.name}", None)
        empty.projectile_props.is_projectile = True

        # Add empty to active collection
        context.collection.objects.link(empty)

        # Set instance object
        self.set_instance_object(empty, ob)

        # Remove instance object (reference is stored in empty projectile props)
        utils.unlink_object_from_all_collections(ob)

        # Set empty as active object
        context.view_layer.objects.active = empty

        return {'FINISHED'}


class PHYSICS_OT_projectile_remove(bpy.types.Operator):
    bl_idname = "rigidbody.projectile_remove_object"
    bl_label = "Remove Object"
    bl_description = "Remove object from as a projectile"

    def get_instance_object(self, ob):
        if "instance_object" in ob.projectile_props:
            return ob.projectile_props["instance_object"]
        return None

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.projectile_props.is_projectile

    def execute(self, context):
        empty = context.object

        ob = self.get_instance_object(empty)

        # Remove empty
        bpy.data.objects.remove(empty, do_unlink=True)

        # Add object to active collection
        context.collection.objects.link(ob)

        # Set object as active
        context.view_layer.objects.active = ob

        return {'FINISHED'}


def launch_instance(ob, properties, settings):
    ob.animation_data_clear()
    ob.hide_viewport = False
    ob.hide_render = False

    # Set start frame
    if bpy.context.scene.frame_start > properties.start_frame:
        properties.start_frame = bpy.context.scene.frame_start

    bpy.context.scene.frame_current = properties.start_frame

    displacement = utils.kinematic_displacement(properties.s, properties.v, 2)
    displacement_rotation = utils.kinematic_rotation(properties.r, properties.w, 2)

    # Hide object
    if properties.start_hidden:
        bpy.context.scene.frame_current -= 1
        ob.hide_viewport = True
        ob.hide_render = True
        ob.keyframe_insert('hide_viewport')
        ob.keyframe_insert('hide_render')

        bpy.context.scene.frame_current += 1
        ob.hide_viewport = False
        ob.hide_render = False
        ob.keyframe_insert('hide_viewport')
        ob.keyframe_insert('hide_render')

    # Set start keyframe
    ob.location = properties.s
    ob.rotation_euler = properties.r
    ob.keyframe_insert('location')
    ob.keyframe_insert('rotation_euler')

    bpy.context.scene.frame_current += 2

    # Set end keyframe
    ob.location = displacement
    ob.rotation_euler = displacement_rotation
    ob.keyframe_insert('location')
    ob.keyframe_insert('rotation_euler')

    # Set animated checkbox
    ob.rigid_body.kinematic = True
    ob.keyframe_insert('rigid_body.kinematic')

    bpy.context.scene.frame_current += 1

    # Set unanimated checkbox
    ob.rigid_body.kinematic = False
    ob.keyframe_insert('rigid_body.kinematic')

# TODO: Rename?
class PHYSICS_OT_projectile_launch(bpy.types.Operator):
    bl_idname = "rigidbody.projectile_launch"
    bl_label = "Launch!"
    bl_description = "Launch the selected object!"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.projectile_props.is_projectile

    def execute(self, context):
        object = context.object
        properties = object.projectile_props
        settings = bpy.context.scene.projectile_settings

        launch_instance(object, properties, settings)

        bpy.context.scene.frame_current = 0

        return {'FINISHED'}

classes = (
    PHYSICS_OT_projectile_add,
    PHYSICS_OT_projectile_remove,
    PHYSICS_OT_projectile_launch,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
