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
    bl_label = "Add Object"
    bl_description = "Set selected object as a projectile"

    @classmethod
    def poll(cls, context):
        if context.object:
            return context.object.type == 'MESH'

    def execute(self, context):
        for object in context.selected_objects:
            if not object.projectile:
                context.view_layer.objects.active = object
                # Make sure it is a rigid body
                if object.rigid_body is None:
                    bpy.ops.rigidbody.object_add()

                # Set as a projectile
                object.projectile = True

                # Now initialize the transforms
                utils.apply_transforms(context)

                # Set start frame
                object.projectile_props.start_frame = context.scene.frame_start

                # Make sure quality is set
                utils.set_quality(context)

        return {'FINISHED'}


class PHYSICS_OT_projectile_remove(bpy.types.Operator):
    bl_idname = "rigidbody.projectile_remove_object"
    bl_label = "Remove Object"
    bl_description = "Remove object from as a projectile"

    @classmethod
    def poll(cls, context):
        if context.object:
            return context.object.projectile

    def execute(self, context):
        for object in context.selected_objects:
            if object.projectile:
                context.view_layer.objects.active = object

                # Remove animation data
                context.active_object.animation_data_clear()

                # Remove rigidbody if not already removed
                if bpy.context.object.rigid_body:
                    bpy.ops.rigidbody.object_remove()

                context.object.projectile = False

                # HACKY! :D
                # Move frame forward, then back to update
                bpy.context.scene.frame_current += 1
                bpy.context.scene.frame_current -= 1

        return {'FINISHED'}


class PHYSICS_OT_projectile_apply_transforms(bpy.types.Operator):
    bl_idname = "rigidbody.projectile_apply_transforms"
    bl_label = "Apply Transforms"
    bl_description = "Set initial position and rotation to current transforms"

    @classmethod
    def poll(cls, context):
        if context.object.projectile:
            return context.object.type == 'MESH'

    def execute(self, context):
        # Apply transforms to all selected projectile objects
        utils.apply_transforms(context)

        return {'FINISHED'}


# TODO: Rename?
class PHYSICS_OT_projectile_launch(bpy.types.Operator):
    bl_idname = "rigidbody.projectile_launch"
    bl_label = "Launch!"
    bl_description = "Launch the selected object!"

    @classmethod
    def poll(cls, context):
        if context.object:
            return context.object.type == 'MESH'

    def execute(self, context):
        object = context.object
        properties = object.projectile_props
        settings = bpy.context.scene.projectile_settings
        object.animation_data_clear()
        object.hide_viewport = False
        object.hide_render = False

        # Set start frame
        if bpy.context.scene.frame_start > properties.start_frame:
            properties.start_frame = bpy.context.scene.frame_start

        bpy.context.scene.frame_current = properties.start_frame

        displacement = utils.kinematic_displacement(properties.s, properties.v, 2)
        displacement_rotation = utils.kinematic_rotation(properties.r, properties.w, 2)

        # Hide object
        if properties.start_hidden:
            bpy.context.scene.frame_current -= 1
            object.hide_viewport = True
            object.hide_render = True
            object.keyframe_insert('hide_viewport')
            object.keyframe_insert('hide_render')

            bpy.context.scene.frame_current += 1
            object.hide_viewport = False
            object.hide_render = False
            object.keyframe_insert('hide_viewport')
            object.keyframe_insert('hide_render')

        # Set start keyframe
        object.location = properties.s
        object.rotation_euler = properties.r
        object.keyframe_insert('location')
        object.keyframe_insert('rotation_euler')

        bpy.context.scene.frame_current += 2

        # Set end keyframe
        object.location = displacement
        object.rotation_euler = displacement_rotation
        object.keyframe_insert('location')
        object.keyframe_insert('rotation_euler')

        # Set animated checkbox
        object.rigid_body.kinematic = True
        object.keyframe_insert('rigid_body.kinematic')

        bpy.context.scene.frame_current += 1

        # Set unanimated checkbox
        object.rigid_body.kinematic = False
        object.keyframe_insert('rigid_body.kinematic')

        bpy.context.scene.frame_current = 0

        if settings.auto_play and not bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()

        return {'FINISHED'}

classes = (
    PHYSICS_OT_projectile_add,
    PHYSICS_OT_projectile_remove,
    PHYSICS_OT_projectile_launch,
    PHYSICS_OT_projectile_apply_transforms,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.projectile_draw_handler = bpy.types.SpaceView3D.draw_handler_add(utils.draw_trajectory, (), 'WINDOW', 'POST_VIEW')
    bpy.app.handlers.load_post.append(utils.subscribe_to_rna_props)

    # Subscribe to properties on first install/register
    # Pass none to avoid argument count mismatch
    utils.subscribe_to_rna_props(None)

    bpy.types.Object.projectile_props = bpy.props.PointerProperty(type=ui.ProjectileObjectProperties)
    bpy.types.Scene.projectile_settings = bpy.props.PointerProperty(type=ui.ProjectileSettings)
    bpy.types.Object.projectile = bpy.props.BoolProperty(name="Projectile")


def unregister():
    if bpy.types.Scene.projectile_draw_handler:
        bpy.types.SpaceView3D.draw_handler_remove(bpy.types.Scene.projectile_draw_handler, 'WINDOW')

    # Remove file load handler for subscribing
    bpy.app.handlers.load_post.remove(utils.subscribe_to_rna_props)

    # Unsubscribe from rna props
    utils.unsubscribe_to_rna_props()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Object.projectile_props
    del bpy.types.Scene.projectile_settings
    del bpy.types.Object.projectile
