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
Use this component to set the 'occupancy' of the building for the PHPP. Be sure to use this component BEFORE using the 'PHPP Res. Appliances' component since the total occupancy is needed in order to estimate the yearly applince energy consumption.
-
Note that by default this component will ONLY set the PHPP values, not the Honeybee load and schedue. If  you would like to set the Honeybee load / schedule to match the PHPP, set the 'set_honeybee_loads_' value to TRUE. This will set the Honyebee occupancy schedule to a 'Constant' schdedule in order to try and approximate the PHPP as closely as possible.
-
EM December 9 , 2020
    Args:
        _HB_model: The Honeybee Model
        set_honeybee_loads_: (bool) Default=False. Set this to TRUE if you would like to set the Honeybee occupant load / schedule to match the PHPP values.
            num_res_units_: (int) Default=1. The total number of residential 'units' in the model. For single-family=1, for multi-family enter the numer of individual dwelling units. For ALL non-residential, leave blank or enter '1'.
        occupancy_: (int) Default=Automatic. The annual average number of occupants. For All residential, leave this blank and the PHPP will calculate this value automatically. Only set it in very unique circumstances. For ALL non-residential, enter the value here.
        -----
        buildingType_: <Optional> Input either: "1-Residential building" or "2-Non-residential building"
        ihgType_: <Optional> Internal Heat Gains Type. Input either: "10-Dwelling", "11-Nursing home / students", "12-Other", "20-Office / Admin. building", "21-School", or "22-Other"
        ihgValues_: <Optional> Internal Heat Gains Source. 
> For Residential, Input either: "2-Standard" or "3-PHPP calculation ('IHG' worksheet)"
> For Non-Residential, input either: "2-Standard" or "4-PHPP calculation ('IHG non-res' worksheet)"
    Returns:
        occupancy_sch_: The Honyebee Schedule which was applied to the model.
        ppl_per_area_: (ppl/m2) The Honeybee Occupant load which was applied to the model.
        HB_model_: The Honeybee Model with the modifications applied.
"""

ghenv.Component.Name = "LBT2PH_SetPHPPOccupancy"
ghenv.Component.NickName = "PHPP Occupancy"
ghenv.Component.Message = 'DEC_09_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import LBT2PH
import LBT2PH.occupancy
import LBT2PH.helpers
import LBT2PH.spaces
import LBT2PH.schedules

reload( LBT2PH )
reload( LBT2PH.occupancy )
reload( LBT2PH.helpers )
reload( LBT2PH.spaces )
reload( LBT2PH.schedules )

#-------------------------------------------------------------------------------
# These are copied from the Honeybee 'ApplyLoadVals' component
try:
    from honeybee_energy.load.people import People
    from honeybee_energy.lib.schedules import schedule_by_identifier
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


if _HB_model:
    #---------------------------------------------------------------------------
    # Calc values to use
    
    phpp_occupancy = LBT2PH.occupancy.Occupancy()
    phpp_occupancy.num_units = num_res_units_
    phpp_occupancy.occupancy = occupancy_
    phpp_occupancy.building_type = buildingType_
    phpp_occupancy.ihg_type = ihgType_
    phpp_occupancy.ihg_values = ihgValues_
    
    tfa = LBT2PH.spaces.get_model_tfa(_HB_model)
    phpp_occupancy.tfa = tfa
    
    phpp_occupancy.check_non_res( ghenv )
    

    #---------------------------------------------------------------------------
    # Assign the HB-Load and HB-Schedule to the HB Rooms
    HB_model_ = _HB_model.duplicate()
    
    if set_honeybee_loads_:
        occupancy_sch_ = LBT2PH.schedules.create_hb_constant_schedule('phpp_occ_sched_constant')
        ppl_per_area_ = phpp_occupancy.occupancy / _HB_model.floor_area
        
        for obj in HB_model_.rooms:
            load = dup_load(obj, 'people', People)
            load.people_per_area = ppl_per_area_
            assign_load(obj, load, 'people')
            
            sched = dup_load(obj, 'people', 'occupancy_sch_')
            sched.occupancy_schedule = schedule_object(occupancy_sch_)
            assign_load(obj, sched, 'people')
    
    #---------------------------------------------------------------------------
    # Add the PHPP info to the User_Data dict
    HB_model_ = LBT2PH.helpers.add_to_HB_model( HB_model_, 'occupancy', phpp_occupancy.to_dict(), ghenv  )