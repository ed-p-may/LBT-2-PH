#
# LBT2PH: A Plugin for creating Passive House Planning Package (PHPP) models from LadybugTools. Created by blgdtyp, llc
# 
# This component is part of the PH-Tools toolkit <https://github.com/PH-Tools>.
# 
# Copyright (c) 2020, bldgtyp, llc <phtools@bldgtyp.com> 
# LBT2PH is free software; you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published 
# by the Free Software Foundation; either version 3 of the License, 
# or (at your option) any later version. 
# 
# LBT2PH is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
# GNU General Public License for more details.
# 
# For a copy of the GNU General Public License
# see <http://www.gnu.org/licenses/>.
# 
# @license GPL-3.0+ <http://spdx.org/licenses/GPL-3.0+>
#
"""
Apply detailed surface parameter values to the opaque faces. Sets the values
in the PHPP 'Areas' Worksheet, Columns: AJ, AK, AL
-
EM March 1, 2021
    Args:
        _hb_objs: Input either Honeybee Faces or Rooms
        shading_factors_: (float) <Optional> Default=0.5.
            Typical values:
            >   Unshaded: approx.. 1
            >   Rural/Suburban areas: approx.. 0.7
            >   Inner City, large roof overhangs, etc.: approx. 0.4
        surface_absorptivities_: (float) <Optional> Default=0.6.
            >   Black: 0.95
            >   Roof tiles: 0.8
            >   White paint: 0.4
            >   Special colours: down to 0.1
            ---
            In case that you only have light reflectance values
            you can convert them into absorption values by
            applying the following formula: Absorption = 1 - Reflection
        surface_emissivities_: (float) <Optional> Default=0.9.
            >   For most building materials: 0.9
            >   Bright ,etal: ca. 0.15
    Returns:
"""

try:  # import the ladybug_rhino dependencies
    from ladybug_rhino.config import tolerance, angle_tolerance
    from honeybee.model import Model
    from honeybee.room import Room
    from honeybee.face import Face
    from honeybee.aperture import Aperture
    from honeybee.door import Door
    from honeybee.shade import Shade
except ImportError as e:
    raise ImportError('\nFailed to import honeybee:\n\t{}'.format(e))

import Grasshopper.Kernel as ghK

import LBT2PH
import LBT2PH.__versions__
import LBT2PH.helpers

reload(LBT2PH)
reload(LBT2PH.__versions__)
reload(LBT2PH.helpers)

ghenv.Component.Name = "LBT2PH Surface Attributes"
LBT2PH.__versions__.set_component_params(ghenv, dev=False)
#-------------------------------------------------------------------------------

def check_value(_val):
    """ Correct for user-error """
    
    if float(_val) > 1.0:
        return _val / 100
    else:
        return _val

def default_get(_list, _index, _default):
    """ In case the user-input len doesn't match, use defaults """
    
    try:
        return check_value(_list[_index])
    except IndexError:
        try:
            return check_value(_list[0])
        except IndexError:
            return check_value(_default)

def create_surface_attr_dict(_i):
    """ Return a dict with the attributes """
    
    attrs = {}
    attrs['Factor_Shading'] = default_get(shading_factors_, _i, 0.5)
    attrs['Factor_Absorptivity'] = default_get(surface_absorptivities_, _i, 0.6)
    attrs['Factor_Emissivity'] = default_get(surface_emissivities_, _i, 0.9)
    
    return attrs

def build_hb_room(_faces, _original_room):
    """ Build a new room, based on the original, but with the new faces """
    
    
    room = Room(_original_room.identifier, _faces, tolerance, angle_tolerance)
    room.display_name = _original_room.display_name
    room.properties.radiance.modifier_set = _original_room.properties.radiance.modifier_set
    room.properties.energy.construction_set = _original_room.properties.energy.construction_set
    room.properties.energy.program_type = _original_room.properties.energy.program_type
    
    return room

# Add the new attributes to the user_data attr on each face
#-------------------------------------------------------------------------------
hb_objs_ = []
for i, hb_obj in enumerate(_hb_objs):
    #---------------------------------------------------------------------------
    if isinstance(hb_obj, Room):
        new_faces = []
        for j, face in enumerate(hb_obj.faces):
            attr_dict = create_surface_attr_dict(j)
            
            new_face = face.duplicate()
            LBT2PH.helpers.add_to_HB_model(new_face, 'phpp', attr_dict, 'overwrite')
            new_faces.append(new_face)
        
        new_faces = tuple(new_faces)
        
        new_room = build_hb_room(new_faces, hb_obj)
        hb_objs_.append(new_room)
    
    #---------------------------------------------------------------------------
    elif isinstance(hb_obj, Face):
        attr_dict = create_surface_attr_dict(i)
        
        new_face = hb_obj.duplicate()
        LBT2PH.helpers.add_to_HB_model(new_face, 'phpp', attr_dict, 'overwrite')
        hb_objs_.append(new_face)
    
    #---------------------------------------------------------------------------
    else:
        msg = "Please input either Honeybee Rooms or Honeybee Faces"
        ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Error, msg)