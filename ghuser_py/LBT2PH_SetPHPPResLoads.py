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
This Component is used to calculate and apply PHPP-Style loads to the Honeybee Rooms. Note that this component should used at the very end and ALL HB-Rooms should be input merged into a single list. It needs to figure out the total building floor area to calc the occupancy, so can't use this on one zone at a time. 
Used this to apply simplified constant-schedule loads which will mimic the PHPP standard values. 
-
EM November 21, 2020
    Args:
        _HBZones: The Honeybee Zones
        num_res_units_: (int) Default=1. 
    Returns:
        HBZones_: The Honeybee Zones
        PHPP_equipmentLoadPerArea_: (W/m2) Elec-Equip load which has been applied to the HB_room(s)
        PHPP_lightingDensityPerArea_: (W/m2) Lighting load which has been applied to the HB_room(s)
        PHPP_numOfPeoplePerArea_: (ppl/m2) Occpancy load which has been applied to the HB_room(s)
        PHPP_occupancySchedule_: Constant Value/always-on Schedule (1) which has been applied to the HB_room(s)
        PHPP_lightingSchedule_: Constant Value/always-on Schedule (1) which has been applied to the HB_room(s)
        PHPP_epuipmentSchedule_: Constant Value/always-on Schedule (1) which has been applied to the HB_room(s)
"""

ghenv.Component.Name = "LBT2PH_SetPHPPResLoads"
ghenv.Component.NickName = "Set HB to PHPP Resi. Loads"
ghenv.Component.Message = 'NOV_21_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import LBT2PH
import LBT2PH.helpers
import LBT2PH.appliances

reload( LBT2PH )
reload( LBT2PH.helpers )
reload( LBT2PH.appliances )

#-------------------------------------------------------------------------------
# These are copied from the Honeybee 'ApplyLoadVals' component
try:
    from honeybee.room import Room
except ImportError as e:
    raise ImportError('\nFailed to import honeybee:\n\t{}'.format(e))

try:
    from honeybee_energy.load.people import People
    from honeybee_energy.load.lighting import Lighting
    from honeybee_energy.load.equipment import ElectricEquipment
    from honeybee_energy.lib.schedules import schedule_by_identifier
    from honeybee_energy.lib.programtypes import program_type_by_identifier
except ImportError as e:
    raise ImportError('\nFailed to import honeybee_energy:\n\t{}'.format(e))
try:
    from ladybug_rhino.grasshopper import all_required_inputs, longest_list
except ImportError as e:
    raise ImportError('\nFailed to import ladybug_rhino:\n\t{}'.format(e))

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

def schedule_object(schedule):
    """Get a schedule object by its identifier or return it it it's already a schedule."""
    if isinstance(schedule, str):
        return schedule_by_identifier(schedule)
    return schedule

def assign_load(hb_obj, load_obj, object_name):
    """Assign a load object to a Room or a ProgramType."""
    try:  # assume it's a Room
        setattr(hb_obj.properties.energy, object_name, load_obj)
    except AttributeError:  # it's a ProgramType
        setattr(hb_obj, object_name, load_obj)


#-------------------------------------------------------------------------------
# Calculate the new HB-Room Loads (Occupancy / Lighting / Elec. Equip)
if _HB_rooms:
    # Occupancy
    num_res_units = num_res_units_ if num_res_units_ else 1
    bldgGrossFloorArea, bldgOcc, PHPP_numOfPeoplePerArea_ = LBT2PH.appliances.calc_occupancy(_HB_rooms, num_res_units)
    
    # Lighting
    PHPP_lightingDensityPerArea_ = LBT2PH.appliances.calc_lighting(_HB_rooms, bldgOcc, bldgGrossFloorArea)
    
    # Appliances
    PHPP_equipmentLoadPerArea_ = LBT2PH.appliances.calc_elec_equip_appliances(_HB_rooms, num_res_units, bldgOcc, bldgGrossFloorArea, ghenv)

#-------------------------------------------------------------------------------
# Create Constant-Value Schedules
PHPP_occupancy_schedule_ = LBT2PH.helpers.create_hb_constant_schedule('phpp_occ_sched_constant')
PHPP_lighting_schedule_ = LBT2PH.helpers.create_hb_constant_schedule('phpp_lighting_sched_constant')
PHPP_epuipment_schedule_ = LBT2PH.helpers.create_hb_constant_schedule('phpp_elec_equip_sched_constant')

#-------------------------------------------------------------------------------
# Apply the new Loads and Schedules onto the HB-Rooms
# This all copied from the Honeybee 'ApplyLoadVals' component
if _HB_rooms:
    # duplicate the initial objects
    HB_rooms_ = []
    for obj in _HB_rooms:
        if isinstance(obj, (Room)):
            HB_rooms_.append(obj.duplicate())
        elif isinstance(obj, str):
            program = program_type_by_identifier(obj)
            HB_rooms_.append(program.duplicate())
        else:
            raise TypeError('Expected Honeybee Room or ProgramType. '
                            'Got {}.'.format(type(obj)))
    
    #---------------------------------------------------------------------------
    # Loads
    # assign the people_per_floor_
    if PHPP_numOfPeoplePerArea_:
        for i, obj in enumerate(HB_rooms_):
            people = dup_load(obj, 'people', People)
            people.people_per_area = PHPP_numOfPeoplePerArea_
            assign_load(obj, people, 'people')
    
    # assign the lighting_per_floor_
    if PHPP_lightingDensityPerArea_:
        for i, obj in enumerate(HB_rooms_):
            lighting = dup_load(obj, 'lighting', Lighting)
            lighting.watts_per_area = PHPP_lightingDensityPerArea_
            assign_load(obj, lighting, 'lighting')
    
    # assign the electric_per_floor_
    if PHPP_equipmentLoadPerArea_:
        for i, obj in enumerate(HB_rooms_):
            equip = dup_load(obj, 'electric_equipment', ElectricEquipment)
            equip.watts_per_area = PHPP_equipmentLoadPerArea_
            assign_load(obj, equip, 'electric_equipment')
    
    #---------------------------------------------------------------------------
    # Schedules
    # assign the occupancy schedule
    if PHPP_occupancy_schedule_:
        for i, obj in enumerate(HB_rooms_):
            people = dup_load(obj, 'people', 'occupancy_sch_')
            people.occupancy_schedule = schedule_object(PHPP_occupancy_schedule_)
            assign_load(obj, people, 'people')
    
    # assign the lighting schedule
    if len(PHPP_lighting_schedule_) != 0:
        for i, obj in enumerate(HB_rooms_):
            lighting = dup_load(obj, 'lighting', 'lighting_sch_')
            lighting.schedule = schedule_object(PHPP_lighting_schedule_)
            assign_load(obj, lighting, 'lighting')
    
    # assign the electric equipment schedule
    if PHPP_epuipment_schedule_:
        for i, obj in enumerate(HB_rooms_):
            equip = dup_load(obj, 'electric_equipment', 'electric_equip_sch_')
            equip.schedule = schedule_object(PHPP_epuipment_schedule_)
            assign_load(obj, equip, 'electric_equipment')