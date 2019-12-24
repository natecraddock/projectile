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

bl_info = {
    "name": "Projectile",
    "author": "Nathan Craddock",
    "version": (1, 0),
    "blender": (2, 81, 0),
    "location": "3D View Sidebar > Physics tab",
    "description": "Set initial velocities for rigid body physics",
    "tracker_url": "",
    "category": "Physics"
}

import bpy
from bpy.app.handlers import persistent

from . import props
from . import ui
from . import ops
from . import utils


# Functions to run on file load
@persistent
def file_load_callback(scene):
    props.subscribe_to_rna_props()

    # Toggle trajectory drawing if enabled in this .blend
    utils.toggle_trajectory_drawing()

def register():
    props.register()
    ui.register()
    ops.register()

    # Add a callback for file load
    bpy.app.handlers.load_post.append(file_load_callback)

    props.subscribe_to_rna_props()
    utils.toggle_trajectory_drawing()

def unregister():
    props.unregister()
    ui.unregister()
    ops.unregister()

    # Remove file load handler
    bpy.app.handlers.load_post.remove(file_load_callback)

    props.unsubscribe_to_rna_props()

    # Remove the draw handler
    ui.PHYSICS_OT_projectle_draw.remove_handler()
