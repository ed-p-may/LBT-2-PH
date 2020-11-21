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
This Component will build out the typical North-American residential appliance set (refrigerator, stove, etc). Note that the default values here will match the PHPP v9.6a and may not be very representative of your specific models / equipment. Refer to your specific equipment for more detailed values to input. Note also that this component will create an appliance set which, by default, is very different than the EnergyPlus values (see the 'PNNL_Resi_Loads' component for detailed E+ values from PNNL sample files.) In many cases, you'll want your PHPP to use the values here for Certification, and then the PNNL values for your EnergyPlus model. You can of course make them both the  same if you want, but usually for Passive House Certification you'll want to use these values here for the PHPP. 
-
This will add the appliances to EACH of the Honeybee zones input. If you only want to add the appliances to one zone or another, use the 'BT_filterZonesByName' component to split up the zones before passing in. Use one of these components for each zone (or each 'type' of zone) to add appliances and things like plug-loads (consumer elec). 
-
Note that this component will ONLY modify the PHPP appliance set, not the EnergyPlus appliance set. In order to  apply these appliances to your EnergyPlus model, use the 'Set PHPP Res Loads' component and Honeybee 'Set Zone Loads'  and 'Set Zone Schedules' components.
- 
EM November 21, 2020
    Args:
        _HBZones: The Honeybee Zones
        _avg_lighting_efficacy: (Lumens / Watt). Avg. Lamp Efficacy, Default=50. Input of the lighting efficiency averaged over all lamps and their duration of use. The lighting efficiency should be reduced by a factor of 0.5 in case of indirect lighting.
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
        refrigerator_kWhDay_: (kWh / day) Default=0.78. Input value here for fridge without a freezer only. For combo units (fridge + freezer) use 'fridgeFreezer_kWhDay_' input instead.
        freezer_kWhDay_: (kWh / day): Default=0.88. Input value here for freezer only. For combo units (fridge + freezer) use 'fridgeFreezer_kWhDay_' input instead.
        fridgeFreezer_kWhDay_: (kWh / day) Defau;t=1.00. Input value here for combo units with fridge + freezer in a single appliance.
        cooking_kWhUse_:  (kWh / use) Typical values include:
> Gas Cooktop: 0.25 kWh/Use.
> Quartz Halogen Ceramic Cooktop: 0.22 kWh/Use
> Induction Ceramic Cooktop: 0.2 kWh/Use
        cooking_Fuel_: Default='1-Electricity'. Input either:
> '1-Electricity'
> '2-Natural gas'
> '3-LPG'
        consumer_elec_: (W) Default=80 W
        other_: (List) A list of up to three additional electricity consuming appliances / equipment (elevators, hot-tubs, etc). Enter each item in the format "Name, kWh/a". So for instance, for an Elevator consuming 600 kWh/a, input the string: "Elevator, 600"
    Returns:
        HBZones_: The Honeybee Zones with new appliances added
"""

ghenv.Component.Name = "LBT2PH_SetResAppliances"
ghenv.Component.NickName = "PHPP Res. Appliances"
ghenv.Component.Message = 'NOV_21_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import LBT2PH
import LBT2PH.appliances

reload( LBT2PH )
reload( LBT2PH.appliances )

def create_appliance(use_defaults_, _name, _ud_input, _utilFac, _freq, _type=None):
    appliance = LBT2PH.appliances.ElecEquipAppliance()
    appliance.name = _name
    appliance.utilization_factor = _utilFac
    appliance.type = _type
    
    if _ud_input:
        appliance.nominal_demand = _ud_input
    elif use_defaults_:
        appliance.nominal_demand = appliance.defaults.get( _name )
    else:
        return None
    
    return appliance

#-------------------------------------------------------------------------------
# Create Appliances, always include Consumer Electronics
dw = create_appliance(use_resi_defaults_, 'dishwasher', dishwasher_kWhUse_, 1, 65, dishwasher_type_ )
cw = create_appliance(use_resi_defaults_, 'clothesWasher', clothesWasher_kWhUse_, 1, 57, clothesWasher_type_ )
cd = create_appliance(use_resi_defaults_, 'clothesDryer', clothesDryer_kWhUse_, 1, 57, clothesDryer_type_ )
fr = create_appliance(use_resi_defaults_, 'fridge', refrigerator_kWhDay_, 1, 365 )
fz = create_appliance(use_resi_defaults_, 'freezer', freezer_kWhDay_, 1, 365 )
ff = create_appliance(use_resi_defaults_, 'fridgeFreezer', fridgeFreezer_kWhDay_, 1, 365 )
ck = create_appliance(use_resi_defaults_, 'clothesDryer', cooking_kWhUse_, 1, 500, cooking_Fuel_ )
ca = create_appliance(use_resi_defaults_, 'consumerElec', consumer_elec_, 1, 0.55)

appliances_list = []
appliances_list.append( dw )
appliances_list.append( cw )
appliances_list.append( cd )
appliances_list.append( fr )
appliances_list.append( fz )
appliances_list.append( ff )
appliances_list.append( ck )
appliances_list.append( ca )

#-------------------------------------------------------------------------------
# Clean up, add some additional info
hb_room_ids = [room.display_name for room in _HB_rooms]
appliances_list = list(filter(None, appliances_list)) 
appliances_obj = LBT2PH.appliances.Appliances( appliances_list, hb_room_ids )
if _avg_lighting_efficacy:
    appliances_obj.lighting_efficacy = _avg_lighting_efficacy

#-------------------------------------------------------------------------------
# Add appliances onto HB Rooms
HB_rooms_ = []
for hb_room in _HB_rooms:
    #---------------------------------------------------------------------------
    # Add HB-room TFA to the appliance
    appliances_obj.host_room_tfa = sum(value.get('_tfa') for value in hb_room.user_data.get('phpp', {}).get('spaces', {}).values())
    
    new_hb_room = hb_room.duplicate()
    
    try:
        user_data = new_hb_room.user_data['phpp'].copy()
    except:
        user_data = { }
    
    user_data.update( {'appliances':appliances_obj.to_dict() } )
    new_hb_room.user_data = {'phpp': user_data}
    
    HB_rooms_.append( new_hb_room )