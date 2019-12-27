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
        return ob and ob.type == 'MESH' and not ob.projectile_props.is_emitter

    def set_instance_object(self, ob, instance):
        ob.projectile_props["instance_object"] = instance

    def set_instances_collection(self, ob, collection):
        ob.projectile_props["instances_collection"] = collection

    def execute(self, context):
        ob = context.object

        # Set object as rigid body
        bpy.ops.rigidbody.object_add()

        # Get parent instance collection
        projectile_collection = utils.get_projectile_collection()
        instances_collection = bpy.data.collections.new(f"instances_{ob.name}")

        projectile_collection.children.link(instances_collection)

        # Create empty
        empty = bpy.data.objects.new(f"emitter_{ob.name}", None)
        empty.projectile_props.is_emitter = True
        empty.location = ob.location

        # Add empty to active collection
        context.collection.objects.link(empty)

        # Set instance object and collection
        self.set_instance_object(empty, ob)
        self.set_instances_collection(empty, instances_collection)

        # Remove instance object (reference is stored in empty projectile props)
        utils.unlink_object_from_all_collections(ob)

        # Set empty as active object
        context.view_layer.objects.active = empty
        empty.select_set(True)
        ob.select_set(False)

        return {'FINISHED'}


class PHYSICS_OT_projectile_remove(bpy.types.Operator):
    bl_idname = "rigidbody.projectile_remove_object"
    bl_label = "Remove Object"
    bl_description = "Remove object from as a projectile"

    def get_instance_object(self, ob):
        if "instance_object" in ob.projectile_props:
            return ob.projectile_props["instance_object"]
        return None

    def get_instances_collection(self, ob):
        if "instances_collection" in ob.projectile_props:
            return ob.projectile_props["instances_collection"]
        return None

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.projectile_props.is_emitter

    def execute(self, context):
        empty = context.object

        ob = self.get_instance_object(empty)
        collection = self.get_instances_collection(empty)

        utils.empty_collection(collection)

        bpy.data.collections.remove(collection)

        # Remove empty
        bpy.data.objects.remove(empty, do_unlink=True)

        # Add object to active collection
        context.collection.objects.link(ob)

        # Set object as active
        context.view_layer.objects.active = ob

        # Remove rigid body from object
        bpy.ops.rigidbody.object_remove()

        # Remove instances collection if empty
        projectile_collection = utils.get_projectile_collection()
        if not len(projectile_collection.children):
            bpy.data.collections.remove(projectile_collection)

        return {'FINISHED'}

def rigid_body_set_active(ob, active, kinematic=True):
    if active:
        ob.rigid_body.collision_collections[0] = True
        ob.rigid_body.collision_collections[19] = False
        ob.rigid_body.kinematic = False
    else:
        ob.rigid_body.collision_collections[0] = False
        ob.rigid_body.collision_collections[19] = True
        ob.rigid_body.kinematic = True

    if kinematic:
        ob.keyframe_insert('rigid_body.kinematic')
    ob.keyframe_insert('rigid_body.collision_collections')

def object_set_visible(ob, visible):
    if visible:
        ob.hide_viewport = False
        ob.hide_render = False
    else:
        ob.hide_viewport = True
        ob.hide_render = True

    ob.keyframe_insert('hide_viewport')
    ob.keyframe_insert('hide_render')

def change_frame(context, offset):
    new_frame = context.scene.frame_current + offset
    context.scene.frame_set(new_frame)

def get_emitter_velocity(context, frame, empty):
    frame_rate = bpy.context.scene.render.fps

    change_frame(context, -1)
    loc_a = empty.matrix_world.to_translation()

    context.scene.frame_set(frame)
    loc_b = empty.matrix_world.to_translation()

    return (loc_b - loc_a) * frame_rate

def launch_instance(ob, properties, settings, frame, empty):
    ob.animation_data_clear()
    ob.hide_viewport = False
    ob.hide_render = False

    # Set start frame
    bpy.context.scene.frame_set(frame)

    # Get emitter velocity
    e_vel = get_emitter_velocity(bpy.context, frame, empty)

    # Calculate velocity
    velocity = properties.v + e_vel

    displacement = utils.kinematic_displacement(empty.matrix_world.to_translation(), velocity, 2)
    displacement_rotation = utils.kinematic_rotation(empty.matrix_world.to_euler(), properties.w, 2)

    change_frame(bpy.context, -1)

    # Hide object
    if properties.start_hidden:
        object_set_visible(ob, False)

    change_frame(bpy.context, 1)

    if properties.start_hidden:
        object_set_visible(ob, True)

    # Set start keyframe
    ob.location = empty.matrix_world.to_translation()
    ob.rotation_euler = empty.matrix_world.to_euler()
    ob.keyframe_insert('location')
    ob.keyframe_insert('rotation_euler')

    change_frame(bpy.context, 2)

    # Set end keyframe
    ob.location = displacement
    ob.rotation_euler = displacement_rotation
    ob.keyframe_insert('location')
    ob.keyframe_insert('rotation_euler')

    # Set animated checkbox
    rigid_body_set_active(ob, False)
    # ob.rigid_body.kinematic = True
    # ob.keyframe_insert('rigid_body.kinematic')

    change_frame(bpy.context, 1)

    # Set unanimated checkbox
    rigid_body_set_active(ob, True)
    # ob.rigid_body.kinematic = False
    # ob.keyframe_insert('rigid_body.kinematic')

    if properties.lifetime > 0:
        bpy.context.scene.frame_set(frame)
        change_frame(bpy.context, properties.lifetime)

        rigid_body_set_active(ob, True)
        object_set_visible(ob, True)
        change_frame(bpy.context, 1)
        rigid_body_set_active(ob, False)
        object_set_visible(ob, False)

# TODO: Rename?
class PHYSICS_OT_projectile_launch(bpy.types.Operator):
    bl_idname = "rigidbody.projectile_launch"
    bl_label = "Launch!"
    bl_description = "Launch the selected object!"

    def get_instance_object(self, empty):
        return empty.projectile_props["instance_object"]

    def get_instances_collection(self, ob):
        if "instances_collection" in ob.projectile_props:
            return ob.projectile_props["instances_collection"]
        return None

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.projectile_props.is_emitter

    def create_instances(self, number, ob, collection):
        PADDING = 4

        for i in range(number):
            name = f"{ob.name}_instance_{str(i).zfill(PADDING)}"
            copy = bpy.data.objects.new(name, ob.data)

            collection.objects.link(copy)

            bpy.context.view_layer.objects.active = copy
            bpy.ops.rigidbody.object_add()


    def execute(self, context):
        empty = context.object
        properties = empty.projectile_props
        settings = context.scene.projectile_settings

        ob = self.get_instance_object(empty)
        collection = self.get_instances_collection(empty)

        # Max instances is the number of frames in the range
        start = properties.start_frame
        end = properties.end_frame
        frames = end - start

        number = min(frames, properties.instance_count)

        step = frames / number

        utils.empty_collection(collection)
        # Create instances
        self.create_instances(number, ob, collection)

        i = start * 1.0
        for o in collection.objects:
            frame = int(i)
            launch_instance(o, properties, settings, frame, empty)
            i += step

        # Reset to ending frame
        bpy.context.scene.frame_current = 0

        bpy.context.view_layer.objects.active = empty

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
