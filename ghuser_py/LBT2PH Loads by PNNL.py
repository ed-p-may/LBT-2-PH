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
This component applies a library of values (Loads and Schedules) which match the 
typical Single Family (SF) residential loads found in the PNNL sample IDF files 
provided by the U.S. Dept of Energy. This includes the Lighting Load/Schedule, 
Occupancy Load/Schedule and Electric-Equipment Load/Schedule. These sample files 
can be found online at https://www.energycodes.gov/development/residential/iecc_models
all values here are from the 2018 IECC, Zone 4a IDF Sample file.
-
Using this component will ONLY set the Honeybee EnergyPlus Room loads and schedules. 
In order to set the PHPP appliance values, use the 'PHPP Res. Appliances' on the 
Honeybee Model (not on the individual rooms).
-
EM March 1, 2021

    Args:
        _HB_rooms: The Honeybee Rooms to apply these values to
        refrigerator_: (W) Default = 91.058
        dishwasher_: (W) Default = 65.699
        clothesWasher_: (W) Default = 28.478 
        clothesDryer_: (W) Default = 213.065
        range_: (W) Default = 248.154
        mel_: (W) Default = 1.713
        plugLoads_: (W) Default = 1.544 
    Returns:
        _HBZones:
        PNNL_ElecEquip_Load_: (W/m2) ElectricEquipment Load which was applied to 
            the Honeybee Rooms input.
        PNNL_Lighting_Load_: (W//m2) Lighting Load which was applied to the 
            Honeybee Rooms input.
        PNNL_Occup_Load_: (PPL/m2) Lighting Load which was applied to the Honeybee Rooms input.
        PNNL_SF_Occup_Sched_: (Fractional) Hourly values (24). Occupancy Schedule 
            which was applied to the Honeybee Rooms input.
        PNNL_SF_Lighting_Sched_: (Fractional) Hourly values (24). Lighting Schedule 
            which was applied to the Honeybee Rooms input.
        PNNL_ElecEquip_Sched_: (Fractional) Hourly values (24). ElectricEquipment 
            Schedule which was applied to the Honeybee Rooms input.
"""

import LBT2PH
import LBT2PH.__versions__
import LBT2PH.appliances

reload( LBT2PH )
reload(LBT2PH.__versions__)
reload( LBT2PH.appliances )

ghenv.Component.Name = "LBT2PH Loads by PNNL"
LBT2PH.__versions__.set_component_params(ghenv, dev=False)

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
    from honeybee_energy.schedule.ruleset import ScheduleRuleset
    from honeybee_energy.lib.scheduletypelimits import schedule_type_limit_by_identifier
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

def build_weekly_hb_schedule(_rm_name, _type, _input_list ):
    
    name = '{}_{}'.format(_rm_name, _type)
    
    sun = _input_list
    mon = _input_list
    tue = _input_list
    wed = _input_list
    thu = _input_list
    fri = _input_list
    sat = _input_list
    hol = _input_list
    
    type_limit = schedule_type_limit_by_identifier('Fractional')
     
    schedule = ScheduleRuleset.from_week_daily_values(
        name, sun, mon, tue, wed, thu, fri, sat,
        hol, timestep=1, schedule_type_limit=type_limit,
        summer_designday_values=None, winter_designday_values=None )
    
    return schedule


# Sort out what loads to us (defaults or User-Determined) for ElecEquip
# ------------------------------------------------------------------------------
pnnl_resi = LBT2PH.appliances.PNNL_ResidentialLoads()

pnnl_resi.set_load( 'refrigerator', refrigerator_ )
pnnl_resi.set_load( 'dishwasher', dishwasher_)
pnnl_resi.set_load( 'clotheswasher', clothesWasher_)
pnnl_resi.set_load( 'clothesdryer', clothesDryer_)
pnnl_resi.set_load( 'stove', range_)
pnnl_resi.set_load( 'mel', mel_)
pnnl_resi.set_load( 'plugloads', plugLoads_)
pnnl_resi.set_load( 'lighting', lighting_)


# Apply new loads and schedules to each Honeybee Room
# ------------------------------------------------------------------------------

HB_rooms_ = []
for hb_room in _HB_rooms:
    # Duplicate the initial Honeybee Room object
    #---------------------------------------------------------------------------
    if isinstance(hb_room, (Room)):
        new_room = hb_room.duplicate()
    elif isinstance(hb_room, str):
        program = program_type_by_identifier(hb_room)
        new_room = program.duplicate()
    else:
        raise TypeError('Expected Honeybee Room or ProgramType. '
                        'Got {}.'.format(type(hb_room)))
    
    # Create the Honeybee-Room Loads
    #---------------------------------------------------------------------------
    PNNL_ElecEquip_Load_  = pnnl_resi.calc_elec_equip_load(hb_room.floor_area)
    PNNL_Lighting_Load_ = pnnl_resi.load('lighting')
    PNNL_Occup_Load_ = pnnl_resi.load('occupancy')
    
    # Create the Honeybee-Room schedules
    #---------------------------------------------------------------------------
    sched_vals_occupancy = pnnl_resi.schedule('occupancy')
    sched_vals_lighting = pnnl_resi.schedule('lighting')
    sched_vals_elec_equip = pnnl_resi.calc_elec_equip_sched(hb_room.floor_area)
    
    PNNL_SF_Occup_Sched_ = build_weekly_hb_schedule(hb_room.display_name, 'Occupancy', sched_vals_occupancy)
    PNNL_SF_Lighting_Sched_ = build_weekly_hb_schedule(hb_room.display_name, 'Lighting', sched_vals_occupancy)
    PNNL_ElecEquip_Sched_ = build_weekly_hb_schedule(hb_room.display_name, 'ElecEquip', sched_vals_occupancy)
    
    # Apply the new Loads / Schedules to the Honeybee Rooms
    #---------------------------------------------------------------------------
    
    # Loads
    #---------------------------------------------------------------------------
    # assign the people_per_floor_
    people = dup_load(new_room, 'people', People)
    people.people_per_area = PNNL_Occup_Load_
    assign_load(new_room, people, 'people')
    
    # assign the lighting_per_floor_
    lighting = dup_load(new_room, 'lighting', Lighting)
    lighting.watts_per_area = PNNL_Lighting_Load_
    assign_load(new_room, lighting, 'lighting')
    
    # assign the electric_per_floor_
    equip = dup_load(new_room, 'electric_equipment', ElectricEquipment)
    equip.watts_per_area = PNNL_ElecEquip_Load_
    assign_load(new_room, equip, 'electric_equipment')
    
    # Schedules
    #---------------------------------------------------------------------------
    # assign the occupancy schedule
    people = dup_load(new_room, 'people', 'occupancy_sch_')
    people.occupancy_schedule = schedule_object(PNNL_SF_Occup_Sched_)
    assign_load(new_room, people, 'people')
    
    # assign the lighting schedule
    lighting = dup_load(new_room, 'lighting', 'lighting_sch_')
    lighting.schedule = schedule_object(PNNL_SF_Lighting_Sched_)
    assign_load(new_room, lighting, 'lighting')
    
    # assign the electric equipment schedule
    equip = dup_load(new_room, 'electric_equipment', 'electric_equip_sch_')
    equip.schedule = schedule_object(PNNL_ElecEquip_Sched_)
    assign_load(new_room, equip, 'electric_equipment')
    
    
    HB_rooms_.append( new_room )