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


# This class holds the handler for drawing trajectories in the 3D view.
# It is wrapped in an operator (singleton) to make it easier to create
# and destroy the handler.
class PHYSICS_OT_projectle_draw(bpy.types.Operator):
    bl_idname = "rigidbody.projectile_draw"
    bl_label = "Draw"
    bl_description = "Trajectory draw handler"

    _handle = None

    @staticmethod
    def add_handler():
        if PHYSICS_OT_projectle_draw._handle is None:
            PHYSICS_OT_projectle_draw._handle = bpy.types.SpaceView3D.draw_handler_add(
                utils.draw_trajectory,
                (),
                'WINDOW',
                'POST_VIEW')

    @staticmethod
    def remove_handler():
        if PHYSICS_OT_projectle_draw._handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(PHYSICS_OT_projectle_draw._handle, 'WINDOW')

        PHYSICS_OT_projectle_draw._handle = None

    def execute(self, context):
        return {'FINISHED'}


class PHYSICS_PT_projectile(bpy.types.Panel):
    bl_label = "Projectile"
    bl_category = "Physics"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        settings = context.scene.projectile_settings

        ob = context.object
        if (ob and ob.projectile_props.is_projectile):
            row = layout.row()
            if(len([object for object in context.selected_objects if object.projectile_props.is_projectile])) > 1:
                row.operator('rigidbody.projectile_remove_object', text="Remove Objects")
            else:
                row.operator('rigidbody.projectile_remove_object')

            if not settings.auto_update:
                row = layout.row()
                row.operator('rigidbody.projectile_launch')

        else:
            row = layout.row()
            if len(context.selected_objects) > 1:
                row.operator('rigidbody.projectile_add_object', text="Add Objects")
            else:
                row.operator('rigidbody.projectile_add_object')


class PHYSICS_PT_projectile_initial_settings(bpy.types.Panel):
    bl_label = "Initial Settings"
    bl_parent_id = "PHYSICS_PT_projectile"
    bl_category = "Physics"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        if context.object and context.object.projectile_props.is_projectile:
            return True
        return False

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        object = context.object

        row = layout.row()
        row.prop(object.projectile_props, 'start_frame')

        row = layout.row()
        row.prop(object.projectile_props, 'start_hidden')

        row = layout.row()
        row.prop(object.projectile_props, 's')

        row = layout.row()
        row.prop(object.projectile_props, 'r')

        row = layout.row()
        row.operator('rigidbody.projectile_apply_transforms')


class PHYSICS_PT_projectile_velocity_settings(bpy.types.Panel):
    bl_label = "Velocity Settings"
    bl_parent_id = "PHYSICS_PT_projectile"
    bl_category = "Physics"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(self, context):
        if context.object and context.object.projectile_props.is_projectile:
            return True
        return False

    def draw(self, context):
        projectile_settings = context.scene.projectile_settings
        layout = self.layout
        layout.use_property_split = True
        object = context.object

        row = layout.row()
        row.prop(context.scene.projectile_settings, 'spherical')

        if projectile_settings.spherical:
            col = layout.column(align=True)
            col.prop(object.projectile_props, 'radius')
            col.prop(object.projectile_props, 'incline')
            col.prop(object.projectile_props, 'azimuth')
        else:
            row = layout.row()
            row.prop(object.projectile_props, 'v')

        row = layout.row()
        row.prop(object.projectile_props, 'w')


class PHYSICS_PT_projectile_settings(bpy.types.Panel):
    bl_label = "Projectile Settings"
    bl_parent_id = "PHYSICS_PT_projectile"
    bl_category = "Physics"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        for object in context.scene.objects:
            if object.projectile_props.is_projectile:
                return True

        return False

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        settings = context.scene.projectile_settings

        row = layout.row()
        row.prop(settings, "quality", expand=True)

        row = layout.row()
        row.prop(settings, "auto_update")

        row = layout.row()
        row.prop(settings, "auto_play")

        row = layout.row()
        row.prop(settings, 'draw_trajectories')


classes = (
    PHYSICS_PT_projectile,
    PHYSICS_PT_projectile_initial_settings,
    PHYSICS_PT_projectile_velocity_settings,
    PHYSICS_PT_projectile_settings,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
