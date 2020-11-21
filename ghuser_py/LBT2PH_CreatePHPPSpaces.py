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
EM November 21, 2020
    Args:
        _HB_rooms: The Honeybee Rooms you would like to build the PHPP Spaces for.
        _TFA_surfaces: <list :Surface> The individual space floor surfaces represting each individual 'space' inside the Honeybee Room (zone).
        _spaces_geometry: <list :PolySurface> Geometry representing the 'space shape' of an individial 'space' or area inside of the Honeybee Room. NOTE: Make sure that your space-shapes are 'open' on the bottom so that they can be joined to the TFA Surfaces to form a closed Brep in the end.
        vent_flowrate_source_: <str> Enter either 'UD' or 'EP' indicating which source should be used to determine the fresh-air flow rates. 'UD' (user-determined) will try and read flow-rates from your Rhino geometry. So make sure that you assigned flow rates to the geometry. 'EP' (EnergyPlus) will try and use the E+/Honeybee Program assigned to the Honyebee Room in order to determine the fresh-air flow rates.
        phpp_vent_schedule_: An optional input for a PHPP-Style ternary ventilation schedule to use for determining flow-rates.
   Returns:
        space_breps_: <Rhino Brep> A list of the space Breps for preview / checking
        phpp_spaces_: A list of the PHPP-Space objects for preview / checking
        HB_rooms_: A list of the Honeybee Rooms with the new PHPP Spaces added.
"""

ghenv.Component.Name = "LBT2PH_CreatePHPPSpaces"
ghenv.Component.NickName = "PHPP Spaces"
ghenv.Component.Message = 'NOV_21_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"


import rhinoscriptsyntax as rs
import Rhino
import ghpythonlib.components as ghc
import Grasshopper.Kernel as ghK
from copy import deepcopy

import LBT2PH
import LBT2PH.helpers
import LBT2PH.spaces
import LBT2PH.ventilation

reload(LBT2PH)
reload(LBT2PH.helpers)
reload(LBT2PH.spaces)
reload(LBT2PH.ventilation)

#
# Make it so you can pass in either Rhino geom (Guid) or GH generated Geometry
#
# ------------------------------------------------------------------------------
# Get the UD Space Geometry
with LBT2PH.helpers.context_rh_doc(ghdoc):
    space_geom = [rs.coercebrep(guid) for guid in _spaces_geometry]
    rhino_tfa_objects = [LBT2PH.spaces.get_tfa_surface_data_from_Rhino(guid) for guid in _TFA_surfaces]

HB_rooms_ = []
if _HB_rooms:
    tfa_objs = {}
    for tfa_srfc_geom, tfa_srfc_name, tfa_srfc_params in rhino_tfa_objects:
        # ----------------------------------------------------------------------
        # Find the TFA's host Room/Zone
        host_room = LBT2PH.spaces.find_tfa_host_room(tfa_srfc_geom, _HB_rooms)
        tfa_obj = LBT2PH.spaces.TFA_Surface(tfa_srfc_geom, host_room, tfa_srfc_params)
        if host_room is None: LBT2PH.spaces.display_host_error(tfa_obj, ghenv)
        
        
        # ----------------------------------------------------------------------
        # Add the new TFA Object to the master dict
        tfa_dict_key = tfa_obj.dict_key
        
        d = { tfa_obj.id : tfa_obj }
        if tfa_dict_key in tfa_objs: tfa_objs[tfa_dict_key].update(d)
        else: tfa_objs[tfa_dict_key] = d


# ------------------------------------------------------------------------------
# Find all the 'touching' TFA surfaces, organize by 'neighbor' into groups
for tfa_obj_list in tfa_objs.values():
    LBT2PH.spaces.find_neighbors( tfa_obj_list )

tfa_srfcs_grouped_by_neighbor = LBT2PH.spaces.bin_tfa_srfcs_by_neighbor(tfa_objs)
tfa_srfcs_cleaned = LBT2PH.spaces.join_touching_tfa_groups(tfa_srfcs_grouped_by_neighbor, ghenv)

# ------------------------------------------------------------------------------
# Build the Spaces for each tfa surface
phpp_spaces_dict = {}
for tfa_srfc in tfa_srfcs_cleaned:
    # See if you can make a closed space Brep
    # If you can, create a new Room Volume from the closed Brep set
    # Then remove that Room's Geom from the set to test (to speed future search?)
    # If no closables match found, create a default space volume
    # If no space geom input, just build a default size space for each
    
    
    # --------------------------------------------------------------------------
    if _spaces_geometry:
        for i, space_geometry in enumerate(space_geom):
            joined_vol = ghc.BrepJoin([space_geometry, tfa_srfc.surface])
            if joined_vol.closed is True:
                new_space_vol = LBT2PH.spaces.Volume( tfa_srfc, joined_vol )
                _spaces_geometry.pop(i)
                break
        else:
            msg = 'Could not join {} with any space geometry.'.format(tfa_srfc.dict_key)
            ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Remark, msg)
            new_space_vol = LBT2PH.spaces.Volume( tfa_srfc )
    else:
        new_space_vol = LBT2PH.spaces.Volume( tfa_srfc )
    
    
    # --------------------------------------------------------------------------
    # Sort the new Space Volume into the master Dict based on name
    if new_space_vol.dict_key in phpp_spaces_dict.keys():
        phpp_spaces_dict[new_space_vol.dict_key].append( new_space_vol )
    else:
        phpp_spaces_dict[new_space_vol.dict_key] = [ new_space_vol ]


#-------------------------------------------------------------------------------
# Build the final PHPP-Spaces from all the the Space Volume Objects
phpp_spaces_ = []

for space_volumes in phpp_spaces_dict.values():
    # Create a single new Room from the list of Room Volumes
    new_space_obj = LBT2PH.spaces.Space( space_volumes )
    phpp_spaces_.append( new_space_obj )



#-------------------------------------------------------------------------------
# Set each Space's fresh-air ventilation flow rates
if 'UD' in str(vent_flowrate_source_).upper(): type = 'UD'
else: type = 'EP'
for hb_room in _HB_rooms:
    # 1)  Figure out the Zone's Annual Average Ventilation Flow Rate
    #     (People + Area) based on HB Program (Load / Schedule)
    #
    # 2) Set the individual PHPP-Space Flow Rates based on the HB Program, or from Rhino Scene
    #
    # 3) If no UD schedule, Calculate the HB/EP Room Flow rates based on the PHPP-Rooms
    
    hb_room_avg_vent_rate = LBT2PH.ventilation.calc_hb_room_annual_vent_flow_rate(hb_room, ghenv)
    hb_room_tfa = sum([space.space_tfa for space in phpp_spaces_ if space.host_room_name == hb_room.display_name])
    
    for space in phpp_spaces_:
        space_vent_flow_rates = LBT2PH.ventilation.calc_space_vent_flow_rates(space, hb_room, hb_room_tfa, hb_room_avg_vent_rate, type, ghenv)
        if space_vent_flow_rates:
            space.set_phpp_vent_rates( space_vent_flow_rates )
        
        if phpp_vent_schedule_:
            space.vent_sched = phpp_vent_schedule_
        else:
            space.vent_sched = LBT2PH.ventilation.calc_space_vent_schedule(space, hb_room, hb_room_tfa)



#-------------------------------------------------------------------------------
# Pack the new space data into the HB Room/Zone object's user_data
HB_rooms_ = []
space_breps_ = []
for hb_room in _HB_rooms:
    # Initialize the new param dict
    user_data = {}
    user_data['phpp'] = {}
    user_data['phpp']['vent_system'] = {}
    user_data['phpp']['spaces'] = {}
    
    
    #---------------------------------------------------------------------------
    # Build a default ventilation system, apply it to the HB Room
    # Add the vent system data to the user_data
    default_ventilation_system = LBT2PH.ventilation.PHPP_Sys_Ventilation(_ghenv=ghenv, _system_id='default')
    user_data['phpp']['vent_system'] = default_ventilation_system.to_dict()
    
    
    #---------------------------------------------------------------------------
    # Add the new PHPP Spaces onto the HB Room
    for phpp_space in phpp_spaces_:
        if hb_room.display_name == phpp_space.host_room_name:
            key = '{}_{}'.format(phpp_space.dict_key, phpp_space.id)
            space = { key : phpp_space.to_dict() }
            user_data['phpp']['spaces'].update( space )
        
        # Grab the brep for preview as well
        space_breps_.extend(phpp_space.space_breps)
    
    
    #---------------------------------------------------------------------------
    # Set the user_data dict on the Honeybee Room with all the new param info
    new_hb_room = hb_room.duplicate()
    new_hb_room.user_data = user_data
    
    HB_rooms_.append(new_hb_room)