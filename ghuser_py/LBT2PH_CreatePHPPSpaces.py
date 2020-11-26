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
Note: Be aware that if you plan on setting the Honeybee Ventilation or Occupancy Loads / Schedules using the Honyebee tools, be sure to that BEFORE you use this component. This component will use those loads/schedules to generate the PHPP values. If you apply those Honeybee loads / schedules AFTER this component, those edits will not be taken into account and your PHPP will not match the Honyebee/E+ model.
-
EM November 26, 2020
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
ghenv.Component.Message = 'NOV_26_2020'
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

try:
    from honeybee_energy.load.ventilation import Ventilation
    from honeybee_energy.lib.schedules import schedule_by_identifier
    from honeybee_energy.lib.programtypes import program_type_by_identifier
    from honeybee_energy.programtype import ProgramType
except ImportError as e:
    raise ImportError('\nFailed to import honeybee_energy:\n\t{}'.format(e))

# This is all from Honeybee 'ApplyLoadVals' Component
#-------------------------------------------------------------------------------
# get the always on schedule
always_on = schedule_by_identifier('Always On')

def dup_load(hb_obj, object_name, object_class):
    """Duplicate a load object assigned to a Room or ProgramType."""
    # try to get the load object assgined to the Room or ProgramType
    try:  # assume it's a Room
        load_obj = hb_obj.properties
        for attribute in ('energy', object_name):
            load_obj = getattr(load_obj, attribute)
    except AttributeError:  # it's a ProgramType
        load_obj = getattr(hb_obj, object_name)

    load_id = '{}_{}'.format(hb_obj.identifier, object_name)
    try:  # duplicate the load object
        dup_load = load_obj.duplicate()
        dup_load.identifier = load_id
        return dup_load
    except AttributeError:  # create a new object
        try:  # assume it's People, Lighting, Equipment or Infiltration
            return object_class(load_id, 0, always_on)
        except:  # it's a Ventilation object
            return object_class(load_id)

def assign_load(hb_obj, load_obj, object_name):
    """Assign a load object to a Room or a ProgramType."""
    try:  # assume it's a Room
        setattr(hb_obj.properties.energy, object_name, load_obj)
    except AttributeError:  # it's a ProgramType
        setattr(hb_obj, object_name, load_obj)

def schedule_object(schedule):
    """Get a schedule object by its identifier or return it it it's already a schedule."""
    if isinstance(schedule, str):
        return schedule_by_identifier(schedule)
    return schedule



# Sort out the UD Space Geometry to use
# ------------------------------------------------------------------------------
with LBT2PH.helpers.context_rh_doc(ghdoc):
    space_geom = [ rs.coercebrep(guid) for guid in _spaces_geometry]

rhino_tfa_objects = []
for i, tfa_input in enumerate(_TFA_surfaces):
    rhino_guid = ghenv.Component.Params.Input[3].VolatileData[0][i].ReferenceID
    rhino_obj = Rhino.RhinoDoc.ActiveDoc.Objects.Find( rhino_guid )
    
    if rhino_obj:
        # Input is a Rhino surface
        with LBT2PH.helpers.context_rh_doc(ghdoc):
            tfa_obj = LBT2PH.spaces.get_tfa_surface_data_from_Rhino( rhino_guid )
            rhino_tfa_objects.append( tfa_obj )
    else:
        # Input is a Grasshoppper-generated surface
        geom = rs.coercegeometry( tfa_input )
        params = {}
        tfa_obj = ( geom, params )
        rhino_tfa_objects.append( tfa_obj )





# Sort the input TFA surfaces depending on which Honeybee Room they are 'in'
# ------------------------------------------------------------------------------
HB_rooms_ = []
tfa_objs = {}
if _HB_rooms:
    for tfa_srfc_geom, tfa_srfc_params in rhino_tfa_objects:
        # ----------------------------------------------------------------------
        # Find the TFA's host Room/Zone
        host_room = LBT2PH.spaces.find_tfa_host_room(tfa_srfc_geom, _HB_rooms)
        tfa_obj = LBT2PH.spaces.TFA_Surface(tfa_srfc_geom, host_room, tfa_srfc_params)
        if host_room is None: LBT2PH.spaces.display_host_error(tfa_obj, ghenv)
        
        
        # Add the new TFA Object to the master dict
        # ----------------------------------------------------------------------
        d = { tfa_obj.id : tfa_obj }
        
        if tfa_obj.dict_key in tfa_objs:
            tfa_objs[tfa_obj.dict_key].update(d)
        else:
            tfa_objs[tfa_obj.dict_key] = d



# Build default / auto PHPP-Space for each HB-Room
# ------------------------------------------------------------------------------
for hb_room in _HB_rooms:
    if not _TFA_surfaces:
        
        tfa_objs_from_hb = LBT2PH.spaces.TFA_Surface.from_hb_room( hb_room, ghenv )
        
        # Add the new TFA Object to the master dict
        # ----------------------------------------------------------------------
        for tfa_obj in tfa_objs_from_hb:
            d = { tfa_obj.id : tfa_obj }
            
            if tfa_obj.dict_key in tfa_objs:
                tfa_objs[tfa_obj.dict_key].update(d)
            else:
                tfa_objs[tfa_obj.dict_key] = d


# Find all the 'touching' TFA surfaces, organize by 'neighbor' into groups
# ------------------------------------------------------------------------------
if tfa_objs:
    for tfa_obj_list in tfa_objs.values():
        LBT2PH.spaces.find_neighbors( tfa_obj_list )

tfa_srfcs_grouped_by_neighbor = LBT2PH.spaces.bin_tfa_srfcs_by_neighbor(tfa_objs)
tfa_srfcs_cleaned = LBT2PH.spaces.join_touching_tfa_groups(tfa_srfcs_grouped_by_neighbor, ghenv)


# Build the Spaces for each tfa surface
# ------------------------------------------------------------------------------
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


# Build the final PHPP-Spaces from all the the Space Volume Objects
#-------------------------------------------------------------------------------
phpp_spaces_ = []

for space_volumes in phpp_spaces_dict.values():
    # Create a single new Room from the list of Room Volumes
    new_space_obj = LBT2PH.spaces.Space( space_volumes )
    phpp_spaces_.append( new_space_obj )



# Set each Space's fresh-air ventilation flow rates
#-------------------------------------------------------------------------------
if 'UD' in str(vent_flowrate_source_).upper(): flow_type = 'UD'
else: flow_type = 'EP'

vent_flows_by_phpp_spaces = {}
for hb_room in _HB_rooms:
    # 1) Figure out the Zone's Nominal (peak) Ventilation Flow Rate
    #    (People + Area + Zone + ACHs) based on HB Program Loads
    #
    # 2) Set the individual PHPP-Space Flow Rates based on the HB Program, or from Rhino Scene
    #
    # 3) If no UD schedule, Calculate the HB/EP Room Flow rates based on the PHPP-Rooms
    #
    # 4) Set the Honeybee Room load / schedule to match the PHPP rates
    #
    
    room_airflow_sup = 0
    room_airflow_eta = 0
    room_airflow_trans = 0
    
    rm_hb_flow_rates = LBT2PH.ventilation.calc_room_vent_rates_from_HB(hb_room, ghenv)
    hb_room_tfa = sum([space.space_tfa for space in phpp_spaces_ if space.host_room_name == hb_room.display_name])
    
    # Calc the PHPP-Space flowrates from the Honeybee-Room
    #---------------------------------------------------------------------------
    for space in phpp_spaces_:
        if space.host_room_name != hb_room.display_name:
            continue
        
        if flow_type == 'EP':
            continue
        
        space_vent_flow_rates = LBT2PH.ventilation.calc_space_vent_rates(space, hb_room, hb_room_tfa, rm_hb_flow_rates.nominal, ghenv)
        if space_vent_flow_rates:
            space.set_phpp_vent_rates( space_vent_flow_rates )
            room_airflow_sup += space_vent_flow_rates.get('V_sup')
            room_airflow_eta += space_vent_flow_rates.get('V_eta')
            room_airflow_trans += space_vent_flow_rates.get('V_trans')
        
        if phpp_vent_schedule_:
            space.vent_sched = phpp_vent_schedule_
        else:
            space.vent_sched = LBT2PH.ventilation.calc_space_vent_schedule(space, hb_room, hb_room_tfa)
    
    
    # Calc the new Honeybee-Room Vent Load and Schedule to match the PHPP-Space
    #---------------------------------------------------------------------------
    if set_honeybee_loads_:
        room_max_airflow = max(room_airflow_sup, room_airflow_eta, room_airflow_trans)
        new_flowrate = ( room_max_airflow / hb_room.floor_area)/3600
        
        vent_flows_by_phpp_spaces[hb_room.identifier] = { 'per_area':new_flowrate, 'per_person':0 }



# Pack the output
#-------------------------------------------------------------------------------
HB_rooms_ = []
space_breps_ = []
const_vent_sched = LBT2PH.helpers.create_hb_constant_schedule( 'PHPP_Const_Vent_Sched' )
for hb_room in _HB_rooms:
    new_hb_room = hb_room.duplicate()
    
   # Set the PHPP Dict values
    #---------------------------------------------------------------------------
    spaces = {}
    for phpp_space in phpp_spaces_:
        if new_hb_room.display_name == phpp_space.host_room_name:
            spaces.update( {phpp_space.dict_key : phpp_space.to_dict()}  )
            
            # Grab the brep for preview as well
            space_breps_.extend(phpp_space.space_breps)
    
    new_hb_room = LBT2PH.helpers.add_to_HB_model(new_hb_room, 'spaces', spaces, ghenv)
    
    
    # Set the Honeybee Ventilation load / schedule
    #---------------------------------------------------------------------------
    if vent_flows_by_phpp_spaces:
        vent_per_floor = vent_flows_by_phpp_spaces.get(hb_room.identifier,{}).get('per_area', None)
        vent_per_person = vent_flows_by_phpp_spaces.get(hb_room.identifier,{}).get('per_person', None)
        
        # vent_per_floor_ Load
        vent = dup_load(new_hb_room, 'ventilation', Ventilation)
        vent.flow_per_area = vent_per_floor
        assign_load(new_hb_room, vent, 'ventilation')
        
        # vent_per_person_ Load (note: gets zero'd out)
        vent = dup_load(new_hb_room, 'ventilation', Ventilation)
        vent.flow_per_person = vent_per_person
        assign_load(new_hb_room, vent, 'ventilation')
        
        ventilation = dup_load(new_hb_room, 'ventilation', 'ventilation_sch_')
        ventilation.schedule = schedule_object(const_vent_sched)
        assign_load(new_hb_room, ventilation, 'ventilation')
    
    
    HB_rooms_.append(new_hb_room)