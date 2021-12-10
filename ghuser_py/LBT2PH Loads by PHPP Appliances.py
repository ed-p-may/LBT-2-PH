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
This Component will build out the typical North-American residential appliance set 
(refrigerator, stove, etc). Note that the default values here will match the PHPP 
v9.6a and may not be very representative of your specific models / equipment. 
Refer to your specific equipment for more detailed values to input. Note also 
that this component will create an appliance set which, by default, is very 
different than the EnergyPlus values (see the 'PNNL_Resi_Loads' component for 
detailed E+ values from PNNL sample files.) In many cases, you'll want your PHPP 
to use the values here for Certification, and then the PNNL values for your 
EnergyPlus model. You can of course make them both the  same if you want, but 
usually for Passive House Certification you'll want to use these values here for 
the PHPP. 
-
This will add the appliances to the entire model. 
-
Note that by default this component will ONLY modify the PHPP appliance set, not 
the EnergyPlus appliance set. In order to apply these loads to your Honeybee model 
as well as the PHPP set the 'set_honeybee_loads_' option to 'True'.
- 
EM March 1, 2021
    Args:
        _HB_model: The Honeybee Model
        use_resi_defaults_: (bool) Default=False. Set this to 'True' in order to
            apply the 'typical' residential appliance package.
        set_honeybee_loads_: (bool) Default=False. Set this to 'True' in order to 
            apply these load values to the Honybee model in addition to the PHPP model.
        _avg_lighting_efficacy: (Lumens / Watt). Avg. Lamp Efficacy, Default=50. 
            Input of the lighting efficiency averaged over all lamps and their duration of use. The lighting efficiency should be reduced by a factor of 0.5 in case of indirect lighting.
            Examples for lighting efficiency [lm/W]:
            > INCANDESCENT BULB < 25 W: 8 LM/W
            > INCANDESCENT BULB < 50 W: 10 LM/W
            > INCANDESCENT BULB < 100 W: 12 LM/W
            > HALOGEN BULB < 50W : 12 LM/W
            > HALOGEN BULB < 100W : 14 LM/W
            > COMPACT FLUORESCENT LAMP < 11 W : 50 LM/W
            > COMPACT FLUORESCENT LAMP < 20 W : 57 LM/W
            > FLUORESCENT LAMP WITH BALLAST: 80 LM/W
            > LED RETRO WHITE: 75 LM/W
            > LED RETRO WARM WHITE: 65 LM/W
            > LED TUBE: 100 LM/W
            --
            Note: LED strips may have substantially lower efficiencies!
        dishwasher_kWhUse_: (kWh / use) Default=1.10
        dishwasher_type_: Default='1-DHW connection'. Input either:
            > '1-DHW connection'
            > '2-Cold water connection'
        clothesWasher_kWhUse_: (kWh / use) Default=1.10. Assume standard 5kg (11 lb) load
        clothesWasher_type_: Default='1-DHW connection'. Input either:
            > '1-DHW connection'
            > '2-Cold water connection'
        clothesDryer_kWhUse_: (kWh / use) Default=3.50
        clothesDryer_type_: Default='4-Condensation dryer'. Input either:
            > '1-Clothes line'
            > '2-Drying closet (cold!)
            > '3-Drying closet (cold!) in extract air'
            > '4-Condensation dryer'
            > '5-Electric exhaust air dryer'
            > '6-Gas exhaust air dryer'
        refrigerator_kWhDay_: (kWh / day) Default=0.78. Input value here for fridge 
            without a freezer only. For combo units (fridge + freezer) use 
            'fridgeFreezer_kWhDay_' input instead.
        freezer_kWhDay_: (kWh / day): Default=0.88. Input value here for freezer 
            only. For combo units (fridge + freezer) use 'fridgeFreezer_kWhDay_' 
            input instead.
        fridgeFreezer_kWhDay_: (kWh / day) Defau;t=1.00. Input value here for combo 
            units with fridge + freezer in a single appliance.
        cooking_kWhUse_:  (kWh / use) Typical values include:
            > Gas Cooktop: 0.25 kWh/Use.
            > Quartz Halogen Ceramic Cooktop: 0.22 kWh/Use
            > Induction Ceramic Cooktop: 0.2 kWh/Use
        cooking_Fuel_: Default='1-Electricity'. Input either:
            > '1-Electricity'
            > '2-Natural gas'
            > '3-LPG'
        consumer_elec_: (W) Default=80 W
        other_: (List) A list of up to three additional electricity consuming 
            appliances / equipment (elevators, hot-tubs, etc). Enter each item in 
            the format "Name, kWh/a". So for instance, for an Elevator consuming 
            600 kWh/a, input the string: "Elevator, 600"
    Returns:
        HBZones_: The Honeybee Zones with new appliances added
"""

import LBT2PH
import LBT2PH.__versions__
import LBT2PH.appliances
import LBT2PH.schedules
import LBT2PH.occupancy
from LBT2PH.helpers import preview_obj

reload( LBT2PH )
reload(LBT2PH.__versions__)
reload( LBT2PH.appliances )
reload( LBT2PH.schedules )
reload( LBT2PH.occupancy )

ghenv.Component.Name = "LBT2PH Loads by PHPP Appliances"
LBT2PH.__versions__.set_component_params(ghenv, dev='MAR_12_21')

#-------------------------------------------------------------------------------
# These are copied from the Honeybee 'ApplyLoadVals' component
try:
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


# Create Appliances, always include Consumer Electronics
#-------------------------------------------------------------------------------
dw = LBT2PH.appliances.ElecEquipAppliance.from_ud(use_resi_defaults_, 'dishwasher', dishwasher_kWhUse_, _type=dishwasher_type_ )
cw = LBT2PH.appliances.ElecEquipAppliance.from_ud(use_resi_defaults_, 'clothesWasher', clothesWasher_kWhUse_, _type=clothesWasher_type_ )
cd = LBT2PH.appliances.ElecEquipAppliance.from_ud(use_resi_defaults_, 'clothesDryer', clothesDryer_kWhUse_, _type=clothesDryer_type_ )
fr = LBT2PH.appliances.ElecEquipAppliance.from_ud(use_resi_defaults_, 'fridge', refrigerator_kWhDay_ )
fz = LBT2PH.appliances.ElecEquipAppliance.from_ud(use_resi_defaults_, 'freezer', freezer_kWhDay_ )
ff = LBT2PH.appliances.ElecEquipAppliance.from_ud(use_resi_defaults_, 'fridgeFreezer', fridgeFreezer_kWhDay_ )
ck = LBT2PH.appliances.ElecEquipAppliance.from_ud(use_resi_defaults_, 'cooking', cooking_kWhUse_, _type=cooking_Fuel_ )
ca = LBT2PH.appliances.ElecEquipAppliance.from_ud(True, 'consumerElec', consumer_elec_)

appliances_list = [dw, cw, cd, fr, fz, ff, ck, ca]

for each in other_[0:2]:
    try:
        name, demand = each.split(',')
    except ValueError:
        name, demand = 'Unnamed', each
    app = LBT2PH.appliances.ElecEquipAppliance.from_ud(use_resi_defaults_, 'other_kWhYear_', demand)
    app.name = name
    
    appliances_list.append( app )

for each in appliances_list:
    preview_obj(each)


# Add to the PHPP User_Data Dict
#-------------------------------------------------------------------------------
HB_model_ = []
if _HB_model:
    # Clean up, add some additional info to the Appliance Set
    #---------------------------------------------------------------------------
    hb_room_ids = [ room.display_name for room in _HB_model.rooms ]
    appliances_list = list(filter(None, appliances_list)) 
    appliance_list_obj = LBT2PH.appliances.ApplianceSet( appliances_list, hb_room_ids )
    if _avg_lighting_efficacy: appliance_list_obj.lighting_efficacy = _avg_lighting_efficacy
    
    
    # Add Appliance List onto HB Model PHPP User_Data Dict
    #---------------------------------------------------------------------------
    HB_model_ = _HB_model.duplicate()
    LBT2PH.helpers.add_to_HB_model(HB_model_, 'appliances', appliance_list_obj.to_dict(), ghenv  )

# Add to the Honeybee Rooms
#-------------------------------------------------------------------------------
if HB_model_ and set_honeybee_loads_:
    new_model = HB_model_.duplicate()
    lighting_schd_ = LBT2PH.schedules.create_hb_constant_schedule('phpp_lighting_sched_constant')
    epuipment_schd = LBT2PH.schedules.create_hb_constant_schedule('phpp_elec_equip_sched_constant')
    
    
    # Calc the Load values for the Honeybee Model Room
    #---------------------------------------------------------------------------
    occupancy_obj = LBT2PH.occupancy.get_model_occupancy(new_model, ghenv)
    occupancy = occupancy_obj.occupancy
    num_units = occupancy_obj.num_units
    
    lighting_per_area = appliance_list_obj.hb_lighting_per_m2(occupancy, new_model.floor_area)
    equipment_per_area = appliance_list_obj.hb_elec_equip_per_m2(occupancy, num_units, new_model.floor_area)
    
    
    # Assign Loads and Schedules
    #---------------------------------------------------------------------------
    for obj in new_model.rooms:
        lighting = dup_load(obj, 'lighting', Lighting)
        lighting.watts_per_area = lighting_per_area
        assign_load(obj, lighting, 'lighting')
    
    for obj in new_model.rooms:
        equip = dup_load(obj, 'electric_equipment', ElectricEquipment)
        equip.watts_per_area = equipment_per_area
        assign_load(obj, equip, 'electric_equipment')
    
    for obj in new_model.rooms:
        lighting = dup_load(obj, 'lighting', 'lighting_sch_')
        lighting.schedule = schedule_object(lighting_schd_)
        assign_load(obj, lighting, 'lighting')
    
    for obj in new_model.rooms:
        equip = dup_load(obj, 'electric_equipment', 'electric_equip_sch_')
        equip.schedule = schedule_object(epuipment_schd)
        assign_load(obj, equip, 'electric_equipment')
    
    HB_model_ = new_model