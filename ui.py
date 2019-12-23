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
        if (ob and ob.projectile):
            row = layout.row()
            if(len([object for object in context.selected_objects if object.projectile])) > 1:
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
        if context.object and context.object.projectile:
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
        if context.object and context.object.projectile:
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
            if object.projectile:
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


class ProjectileObjectProperties(bpy.types.PropertyGroup):
    start_frame: bpy.props.IntProperty(
        name="Start Frame",
        description="Frame to start velocity initialization on",
        default=1,
        options={'HIDDEN'},
        update=utils.update_callback
    )

    s: bpy.props.FloatVectorProperty(
        name="Initial Location",
        description="Initial position for the object",
        subtype='TRANSLATION',
        precision=4,
        options={'HIDDEN'},
        update=utils.update_callback
    )

    r: bpy.props.FloatVectorProperty(
        name="Rotation",
        description="Initial rotation for the object",
        precision=4,
        options={'HIDDEN'},
        subtype='EULER',
        update=utils.update_callback
    )

    v: bpy.props.FloatVectorProperty(
        name="Velocity",
        description="Velocity for the object",
        subtype='VELOCITY',
        precision=4,
        options={'HIDDEN'},
        update=utils.velocity_callback
    )

    w: bpy.props.FloatVectorProperty(
        name="Angular Velocity",
        description="Angular velocity for the object",
        subtype='EULER',
        precision=4,
        options={'HIDDEN'},
        update=utils.update_callback
    )

    start_hidden: bpy.props.BoolProperty(
        name="Start Hidden",
        description="Hide the object before the start frame",
        default=False,
        options={'HIDDEN'},
        update=utils.update_callback
    )

    radius: bpy.props.FloatProperty(
        name="Radius",
        description="Radius (magnitude) of velocity",
        default=0.0,
        unit='VELOCITY',
        options={'HIDDEN'},
        update=utils.spherical_callback
    )

    incline: bpy.props.FloatProperty(
        name="Incline",
        description="Incline (theta) for velocity",
        default=0.0,
        unit='ROTATION',
        options={'HIDDEN'},
        update=utils.spherical_callback
    )

    azimuth: bpy.props.FloatProperty(
        name="Azimuth",
        description="Azimuth (phi) for velocity",
        default=0.0,
        unit='ROTATION',
        options={'HIDDEN'},
        update=utils.spherical_callback
    )


class ProjectileSettings(bpy.types.PropertyGroup):
    draw_trajectories: bpy.props.BoolProperty(
        name="Draw Trajectories",
        description="Draw projectile trajectories in the 3D view",
        options={'HIDDEN'},
        default=True,
        update=utils.draw_trajectories_callback
    )

    auto_update: bpy.props.BoolProperty(
        name="Auto Update",
        description="Update the rigidbody simulation after property changes",
        options={'HIDDEN'},
        default=True
    )

    auto_play: bpy.props.BoolProperty(
        name="Auto Play",
        description="Start animation playback after any changes",
        options={'HIDDEN'},
        default=False
    )

    quality: bpy.props.EnumProperty(
        name="Quality",
        items=[("low", "Low", "Use low quality solver settings"),
               ("medium", "Medium", "Use medium quality solver settings"),
               ("high", "High", "Use high quality solver settings")],
        default='medium',
        options={'HIDDEN'},
        update=utils.set_quality_callback)

    spherical: bpy.props.BoolProperty(
        name="Spherical",
        description="Set velocity with spherical coordinates",
        options={'HIDDEN'},
        default=False
    )


classes = (
    ProjectileObjectProperties,
    ProjectileSettings,
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
