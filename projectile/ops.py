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

# Find first collection object is in
def get_object_collection(ob):
    for collection in bpy.data.collections:
        if ob.name in collection.objects:
            return collection
    # Try the scene collection
    if ob.name in bpy.context.scene.collection:
        return bpy.context.scene.collection
    return None

class PHYSICS_OT_projectile_add(bpy.types.Operator):
    bl_idname = "rigidbody.projectile_add_emitter"
    bl_label = "New Emitter"
    bl_description = "Create a new emitter with the active object as the instances"

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
        object_collection = get_object_collection(ob)

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

        # Add empty to collection the object was in
        object_collection.objects.link(empty)

        # Set instance object and collection
        self.set_instance_object(empty, ob)
        self.set_instances_collection(empty, instances_collection)

        # Remove instance object (reference is stored in empty projectile props)
        utils.unlink_object_from_all_collections(ob)

        # Set empty as active object
        context.view_layer.objects.active = empty
        empty.select_set(True)
        ob.select_set(False)

        # Run the operator
        bpy.ops.rigidbody.projectile_execute()

        # Ensure quality is set
        utils.set_quality(context)

        return {'FINISHED'}


def get_instance_object(ob):
    if "instance_object" in ob.projectile_props:
        return ob.projectile_props["instance_object"]
    return None

def get_instances_collection(ob):
    if "instances_collection" in ob.projectile_props:
        return ob.projectile_props["instances_collection"]
    return None

class PHYSICS_OT_projectile_remove(bpy.types.Operator):
    bl_idname = "rigidbody.projectile_remove_emitter"
    bl_label = "Remove Emitter"
    bl_description = "Remove emitter and all instances"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.projectile_props.is_emitter

    def execute(self, context):
        empty = context.object
        emitter_collection = get_object_collection(empty)

        ob = get_instance_object(empty)
        collection = get_instances_collection(empty)

        utils.empty_collection(collection)

        bpy.data.collections.remove(collection)

        # Remove empty
        bpy.data.objects.remove(empty, do_unlink=True)

        # Add object to collection that empty was just removed from
        emitter_collection.objects.link(ob)

        # Set object as active
        context.view_layer.objects.active = ob

        # Remove instances collection if empty
        projectile_collection = utils.get_projectile_collection()
        if not len(projectile_collection.children):
            bpy.data.collections.remove(projectile_collection)

        return {'FINISHED'}


def change_frame(context, offset):
    new_frame = context.scene.frame_current + offset
    context.scene.frame_set(new_frame)

class Instance:
    """ A projectile instance """

    def __str__(self):
        return f"{self.ob.name} start:{self.start_frame} end:{self.end_frame}"

    def __init__(self, ob, emitter):
        props = emitter.projectile_props

        self.ob = ob
        self.lifetime = props.lifetime
        self.v = props.v.copy()
        self.w = props.w.copy()

        self.emitter = emitter

    # Set beginning location, rotation, and other properties
    def initialize(self, start_frame):
        self.start_hidden = self.emitter.projectile_props.start_hidden
        self.start_frame = start_frame
        self.end_frame = start_frame + self.lifetime

        self.velocity = self.get_emitter_velocity(bpy.context, start_frame) + self.v

    def activate(self):
        self.set_visible(True)

        if self.start_hidden:
            change_frame(bpy.context, -1)
            self.set_visible(False)
            change_frame(bpy.context, 1)

    def execute(self):
        displacement = utils.kinematic_displacement(self.emitter.matrix_world.to_translation(), self.velocity, 2)
        displacement_rotation = utils.kinematic_rotation(self.emitter.matrix_world.to_euler(), self.w, 2)

        # Set start keyframe
        self.ob.location = self.emitter.matrix_world.to_translation()
        self.ob.rotation_euler = self.emitter.matrix_world.to_euler()
        self.ob.keyframe_insert('location')
        self.ob.keyframe_insert('rotation_euler')

        change_frame(bpy.context, 2)

        # Set end keyframe
        self.ob.location = displacement
        self.ob.rotation_euler = displacement_rotation
        self.ob.keyframe_insert('location')
        self.ob.keyframe_insert('rotation_euler')

        # Set animated checkbox
        self.set_active(False)

        change_frame(bpy.context, 1)

        # Set unanimated checkbox
        self.set_active(True)

    def deactivate(self):
        self.set_active(True)
        self.set_visible(True)

        change_frame(bpy.context, 1)

        self.set_active(False)
        self.set_visible(False)

    def set_active(self, active):
        if active:
            self.ob.rigid_body.collision_collections[0] = True
            self.ob.rigid_body.collision_collections[19] = False
            self.ob.rigid_body.kinematic = False
        else:
            self.ob.rigid_body.collision_collections[0] = False
            self.ob.rigid_body.collision_collections[19] = True
            self.ob.rigid_body.kinematic = True

        self.ob.keyframe_insert('rigid_body.kinematic')
        self.ob.keyframe_insert('rigid_body.collision_collections')

    def set_visible(self, visible):
        if visible:
            self.ob.hide_viewport = False
            self.ob.hide_render = False
        else:
            self.ob.hide_viewport = True
            self.ob.hide_render = True

        self.ob.keyframe_insert('hide_viewport')
        self.ob.keyframe_insert('hide_render')

    def get_emitter_velocity(self, context, frame):
        frame_rate = context.scene.render.fps

        loc_b = self.emitter.matrix_world.to_translation()

        change_frame(context, -1)
        loc_a = self.emitter.matrix_world.to_translation()
        change_frame(context, 1)

        return (loc_b - loc_a) * frame_rate

class PHYSICS_OT_projectile_execute(bpy.types.Operator):
    bl_idname = "rigidbody.projectile_execute"
    bl_label = "Execute "
    bl_description = "Create instances based on current emitter settings"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.projectile_props.is_emitter

    def create_instance(self, ob, collection, empty):
        PADDING = 4

        name = f"{ob.name}_instance"
        instance = bpy.data.objects.new(name, ob.data)

        # Store a link to the emitter in the instance
        instance.projectile_props["emitter"] = empty

        collection.objects.link(instance)

        bpy.context.view_layer.objects.active = instance
        bpy.ops.rigidbody.object_add()

        projectile_props = empty.projectile_props
        instance.rigid_body.friction = projectile_props.friction
        instance.rigid_body.restitution = projectile_props.bounciness
        instance.rigid_body.collision_shape = projectile_props.collision_shape

        return Instance(instance, empty)

    def execute(self, context):
        empty = context.object
        properties = empty.projectile_props
        pool = []
        instances = []

        ob = get_instance_object(empty)
        collection = get_instances_collection(empty)

        # Max instances is the number of frames in the range
        start = properties.start_frame
        end = properties.end_frame
        frames = end - start

        number = min(frames, properties.instance_count)

        step = frames / number

        utils.empty_collection(collection)

        # Create list of frames for new instances
        instance_frames = []
        for i in range(number):
            instance_frames.append(start + int(i * step))

        # Create instances
        for frame in range(start, end + 1):

            # Check if a new instance is created on this frame
            if frame in instance_frames:
                # Get or create an instance to animate
                context.scene.frame_set(frame)
                if pool:
                    instance = pool.pop()
                else:
                    instance = self.create_instance(ob, collection, empty)

                # Set initial position, rotation, frame for instance
                instances.append(instance)
                instance.initialize(frame)

                instance.activate()
                instance.execute()

            # Check if an instance is to be destroyed
            if instances and instances[0].lifetime and instances[0].end_frame == frame:
                context.scene.frame_set(frame)

                instances[0].deactivate()

                # Remove and add to the pool to be reused later
                instance = instances.pop(0)
                pool.append(instance)


        # Reset to starting frame
        bpy.context.scene.frame_current = 0

        bpy.context.view_layer.objects.active = empty

        # Clear dirty
        properties.is_dirty = False

        return {'FINISHED'}


class PHYSICS_OT_projectile_execute_all(bpy.types.Operator):
    bl_idname = "rigidbody.projectile_execute_all"
    bl_label = "Execute All"
    bl_description = "Apply settings for all emitters that need updating"

    def execute(self, context):
        emitters = [ob for ob in context.scene.objects if ob.projectile_props.is_emitter]

        for emitter in emitters:
            if emitter.projectile_props.is_dirty:
                context.view_layer.objects.active = emitter
                bpy.ops.rigidbody.projectile_execute()

        return {'FINISHED'}

classes = (
    PHYSICS_OT_projectile_add,
    PHYSICS_OT_projectile_remove,
    PHYSICS_OT_projectile_execute,
    PHYSICS_OT_projectile_execute_all,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
